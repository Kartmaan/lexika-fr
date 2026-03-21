"""
core/dictionary.py
------------------
Interface between the application and the SQLite dictionary database.
All SQL queries are centralized here.
"""

import json
import sqlite3
import difflib
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Optional

# Minimum word length for partial anagram results.
# Words shorter than this will never appear in sub-anagram searches.
# Change this value to adjust the minimum length globally.
MIN_PARTIAL_ANAGRAM_LENGTH = 3

def _normalize(text: str) -> str:
    """Removes accents from a string for comparison purposes."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

# Accented variants for each base letter (used in indexed LIKE queries)
_ACCENT_VARIANTS = {
    'a': 'àâä',
    'e': 'éèêë',
    'i': 'îï',
    'o': 'ôöœ',
    'u': 'ùûü',
    'c': 'ç',
}

class Dictionary:
    """
    Handles read access to the French SQLite dictionary database.

    Expected schema:
        TABLE mots (id, forme TEXT, pos TEXT, definitions TEXT)
        INDEX idx_forme ON mots(forme)
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    # ------------------------------------------------------------------
    # Exact search
    # ------------------------------------------------------------------

    def search(self, word: str) -> Optional[list[dict]]:
        """
        Returns the list of lexemes for an exact word match, or None if not found.

        Each element is a dict:
            { "pos": "N", "definitions": [ {...}, ... ] }
        """
        word = word.strip().lower()
        if not word:
            return None
        cursor = self._conn.cursor()
        cursor.execute("SELECT pos, definitions FROM mots WHERE forme = ?", (word,))
        rows = cursor.fetchall()
        if not rows:
            return None
        return [
            {"pos": row["pos"], "definitions": json.loads(row["definitions"])}
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Similar word suggestions (accent-aware)
    # ------------------------------------------------------------------

    def suggest(self, word: str, n: int = 8) -> list[str]:
        """
        Returns up to n words close to the user's input.
        Handles missing accents: 'element' -> ['élément', ...]
        """
        word = word.strip().lower()
        if not word:
            return []

        word_norm = _normalize(word)
        cursor = self._conn.cursor()

        # Pass 1: accent-aware prefix queries (indexed, fast)
        prefixes = self._prefixes_with_variants(word_norm, length=3)
        placeholders = " OR ".join(["forme LIKE ?"] * len(prefixes))
        params = [f"{p}%" for p in prefixes]
        cursor.execute(
            f"SELECT DISTINCT forme FROM mots WHERE {placeholders} LIMIT 600",
            params
        )
        candidates = [row["forme"] for row in cursor.fetchall()]

        # Pass 2: supplement if few results
        if len(candidates) < 20 and len(word_norm) >= 2:
            prefixes2 = self._prefixes_with_variants(word_norm[1:], length=2)
            ph2 = " OR ".join(["forme LIKE ?"] * len(prefixes2))
            params2 = [f"%{p}%" for p in prefixes2]
            cursor.execute(
                f"SELECT DISTINCT forme FROM mots WHERE {ph2} LIMIT 300",
                params2
            )
            seen = set(candidates)
            for row in cursor.fetchall():
                if row["forme"] not in seen:
                    candidates.append(row["forme"])
                    seen.add(row["forme"])

        if not candidates:
            return []

        # Pass 3: rank by similarity on normalized forms
        norm_to_orig: dict[str, str] = {}
        for c in candidates:
            c_norm = _normalize(c)
            if c_norm not in norm_to_orig:
                norm_to_orig[c_norm] = c

        close_norm = difflib.get_close_matches(
            word_norm, list(norm_to_orig.keys()), n=n * 2, cutoff=0.65
        )
        results = [norm_to_orig[p] for p in close_norm if p in norm_to_orig]

        if not results and candidates:
            results = candidates[:n]

        return results[:n]

    def _prefixes_with_variants(self, base: str, length: int) -> list[str]:
        """
        Generates LIKE prefixes including accented variants.
        e.g. 'ele' -> ['ele', 'éle', 'èle', 'êle', 'ële']
        """
        prefix = base[:length]
        variants: set[str] = {prefix}
        for i, letter in enumerate(prefix):
            if letter in _ACCENT_VARIANTS:
                for accented in _ACCENT_VARIANTS[letter]:
                    variants.add(prefix[:i] + accented + prefix[i + 1:])
        return list(variants)

    # ------------------------------------------------------------------
    # Analyzer: multi-criteria filtering
    # ------------------------------------------------------------------

    def analyze(
        self,
        length:          int | None       = None,
        start_with:      str | None       = None,
        end_with:        str | None       = None,
        contains:        list[str]        = None,
        not_contain:     list[str]        = None,
        nth_letters:     list[list]       = None,
        anagram:         list[str] | None = None,
        partial_anagram: bool             = False,
        no_comp:         bool             = True,
        limit:           int              = 500,
    ) -> tuple[list[str], bool]:
        """
        Filters the dictionary using cascading SQL conditions,
        with a Python-side post-filter for anagram matching.

        Parameters
        ----------
        length          : exact word length in characters
        start_with      : prefix the word must start with
        end_with        : suffix the word must end with
        contains        : list of letters the word must contain (each at least once)
        not_contain     : list of letters the word must NOT contain
        nth_letters     : list of [position, letter] pairs (1-indexed)
                          e.g. [[2, 'r'], [4, 't']] -> 2nd letter is 'r', 4th is 't'
        anagram         : list of letters for anagram matching
        partial_anagram : if True, also return words that use a SUBSET of the
                          anagram letters (sub-anagrams), e.g. 'carte' -> 'car', 'rat'
                          Words shorter than MIN_PARTIAL_ANAGRAM_LENGTH are excluded.
                          Ignored when anagram is None.
        no_comp         : if True (default), excludes compound words (space or hyphen)
        limit           : maximum number of results returned (default 500)

        Returns
        -------
        (words: list[str], truncated: bool)
            words      : matching word forms, sorted alphabetically
            truncated  : True if results were cut off at the limit
        """
        conditions = [] # SQL WHERE conditions
        params = [] # SQL parameters for the conditions

        # Anagram setup
        anagram_sorted  = None
        anagram_counter = None
        if anagram:
            letters = [_normalize(l).lower() for l in anagram if l.strip()]
            anagram_sorted  = sorted(letters)
            anagram_counter = Counter(letters)

            if partial_anagram:
                # Partial mode: words can use any subset of the pool.
                # SQL bounds: length >= MIN_PARTIAL_ANAGRAM_LENGTH
                #             length <= len(pool)  (can't use more letters than available)
                # The exact Python check replaces the sorted() equality test.
                if length is None:
                    # Add both bounds as SQL conditions
                    pass   # handled below after length block
            else:
                # Perfect anagram: word must use ALL letters exactly once.
                if length is None:
                    length = len(letters)

        # --- Build SQL WHERE clauses ---

        if length is not None:
            conditions.append("LENGTH(forme) = ?")
            params.append(length)
        elif anagram and partial_anagram:
            # Partial anagram: bound by [MIN, pool_size] instead of exact length
            pool_size = len([l for l in anagram if l.strip()])
            conditions.append("LENGTH(forme) >= ?")
            params.append(MIN_PARTIAL_ANAGRAM_LENGTH)
            conditions.append("LENGTH(forme) <= ?")
            params.append(pool_size)

        if start_with:
            conditions.append("forme LIKE ?")
            params.append(f"{start_with.lower()}%")

        if end_with:
            conditions.append("forme LIKE ?")
            params.append(f"%{end_with.lower()}")

        if contains:
            for letter in contains:
                if letter.strip():
                    conditions.append("forme LIKE ?")
                    params.append(f"%{letter.lower()}%")

        if not_contain:
            for letter in not_contain:
                if letter.strip():
                    conditions.append("forme NOT LIKE ?")
                    params.append(f"%{letter.lower()}%")

        if nth_letters:
            for pair in nth_letters:
                if len(pair) == 2:
                    pos, letter = pair
                    try:
                        pos = int(pos)
                        letter = str(letter).lower().strip()
                        if pos >= 1 and letter:
                            # SQLite SUBSTR is 1-indexed
                            conditions.append("SUBSTR(forme, ?, 1) = ?")
                            params.extend([pos, letter])
                    except (ValueError, TypeError):
                        pass

        if no_comp:
            # Exclude words containing a space or a hyphen
            conditions.append("forme NOT LIKE '% %'")
            conditions.append("forme NOT LIKE '%-%'")

        # Require at least one active condition to prevent full-table scans
        if not conditions:
            return [], False

        where_clause = " AND ".join(conditions)

        cursor = self._conn.cursor()

        if anagram_sorted:
            # When searching for anagrams, LENGTH(forme) already bounds the
            # result set tightly enough. Removing the SQL LIMIT ensures we
            # never miss words that appear late in the alphabet (e.g. 'niche'
            # when searching anagrams of 'chien').
            sql = (
                f"SELECT DISTINCT forme FROM mots "
                f"WHERE {where_clause} "
                f"ORDER BY forme"
            )
            cursor.execute(sql, params)
        else:
            # For non-anagram searches apply the limit directly in SQL.
            sql = (
                f"SELECT DISTINCT forme FROM mots "
                f"WHERE {where_clause} "
                f"ORDER BY forme LIMIT ?"
            )
            params.append(limit + 1)
            cursor.execute(sql, params)

        words = [row["forme"] for row in cursor.fetchall()]

        # Python post-filter: anagram check
        if anagram_sorted:
            if partial_anagram:
                # Sub-anagram: every letter of the word must be available
                # in the pool (with correct multiplicity).
                def _is_sub_anagram(word: str) -> bool:
                    word_counter = Counter(_normalize(word).lower())
                    for letter, count in word_counter.items():
                        if anagram_counter.get(letter, 0) < count:
                            return False
                    return True
                words = [w for w in words if _is_sub_anagram(w)]
            else:
                # Perfect anagram: sorted letters must match exactly.
                words = [
                    w for w in words
                    if sorted(_normalize(w).lower()) == anagram_sorted
                ]

        truncated = len(words) > limit
        return sorted(words[:limit]), truncated

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def word_exists(self, word: str) -> bool:
        """Quickly checks whether a word form exists in the dictionary."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT 1 FROM mots WHERE forme = ? LIMIT 1",
            (word.strip().lower(),)
        )
        return cursor.fetchone() is not None

    def close(self):
        """Closes the SQLite connection cleanly."""
        if self._conn:
            self._conn.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass