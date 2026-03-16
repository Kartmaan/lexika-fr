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
from pathlib import Path
from typing import Optional

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
            raise FileNotFoundError(
                f"Database not found: {self.db_path}"
            )
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
        return [{"pos": row["pos"], "definitions": json.loads(row["definitions"])} for row in rows]

    # ------------------------------------------------------------------
    # Similar word suggestions (accent-aware)
    # ------------------------------------------------------------------

    def suggest(self, word: str, n: int = 8) -> list[str]:
        """
        Returns up to n words close to the user's input.

        Handles missing accents: 'element' → ['élément', ...]
        Strategy:
          1. Normalize input (strip accents)
          2. Build accent-aware LIKE prefixes (indexed queries)
          3. Rank candidates with difflib on normalized forms
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

        # Fallback: return first candidates if difflib finds nothing
        if not results and candidates:
            results = candidates[:n]

        return results[:n]

    def _prefixes_with_variants(self, base: str, length: int) -> list[str]:
        """
        Generates LIKE prefixes including accented variants.
        e.g. 'ele' → ['ele', 'éle', 'èle', 'êle', 'ële']
        """
        prefix = base[:length]
        variants: set[str] = {prefix}
        for i, letter in enumerate(prefix):
            if letter in _ACCENT_VARIANTS:
                for accented in _ACCENT_VARIANTS[letter]:
                    variants.add(prefix[:i] + accented + prefix[i + 1:])
        return list(variants)

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
