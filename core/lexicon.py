"""
core/lexicon.py
---------------
Full management of the personal lexicon (saved words).
Data is stored in a local JSON file.

lexicon.json format:
{
    "word": {
        "source": "dictionary" | "custom",
        "lexemes": [
            {
                "pos": "N",
                "gender": "m",
                "definitions": [
                    {
                        "gloss": "...",
                        "register": null,
                        "semantic": null,
                        "domain": null,
                        "examples": [],
                        "sub_definitions": []
                    }
                ]
            }
        ]
    }
}
"""

import json
from pathlib import Path
from typing import Optional

class Lexicon:
    """
    Manages the user's personal lexicon.
    All changes are immediately persisted to disk.
    """

    def __init__(self, json_path: str | Path):
        self.json_path = Path(json_path)
        self._data: dict = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        """Loads the JSON file, creates an empty lexicon if it does not exist."""
        if self.json_path.exists():
            with open(self.json_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
            self._save()

    def _save(self):
        """Persists data to disk."""
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def words(self) -> list[str]:
        """Returns the list of words sorted alphabetically."""
        return sorted(self._data.keys(), key=lambda w: w.lower())

    def contains(self, word: str) -> bool:
        """Checks whether a word is already in the lexicon."""
        return word.strip().lower() in self._data

    def get(self, word: str) -> Optional[dict]:
        """Returns the full entry for a word, or None if absent."""
        return self._data.get(word.strip().lower())

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def word_count(self) -> int:
        return len(self._data)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_from_dictionary(self, word: str, lexemes: list[dict]) -> bool:
        """
        Adds a word sourced from the dictionary.
        Returns False if the word is already present.
        """
        key = word.strip().lower()
        if key in self._data:
            return False
        self._data[key] = {
            "source": "dictionary",
            "lexemes": lexemes,
        }
        self._save()
        return True

    def add_custom(self, word: str, definitions: list[str]) -> bool:
        """
        Adds a custom word entered by the user.
        definitions: list of strings (one per definition).
        Returns False if the word is already present.
        """
        key = word.strip().lower()
        if key in self._data:
            return False

        lexemes = [
            {
                "pos":    "?",
                "gender": None,   # custom words have no gender by default
                "definitions": [
                    {
                        "gloss": d.strip(),
                        "register": None,
                        "semantic": None,
                        "domain": None,
                        "examples": [],
                        "sub_definitions": [],
                    }
                    for d in definitions
                    if d.strip()
                ],
            }
        ]
        self._data[key] = {
            "source": "custom",
            "lexemes": lexemes,
        }
        self._save()
        return True

    def remove(self, word: str) -> bool:
        """
        Removes a word from the lexicon.
        Returns False if the word was not present.
        """
        key = word.strip().lower()
        if key not in self._data:
            return False
        del self._data[key]
        self._save()
        return True

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def export(self, path: str | Path) -> bool:
        """
        Exports the lexicon to a JSON file chosen by the user.
        Returns True on success.
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def import_from(self, path: str | Path) -> tuple[bool, str]:
        """
        Imports a lexicon from a JSON file.
        Existing words are preserved; new ones are merged in.
        Returns (success: bool, message: str).
        """
        try:
            path = Path(path)
            with open(path, "r", encoding="utf-8") as f:
                new_data = json.load(f)

            if not isinstance(new_data, dict):
                return False, "Invalid format: the JSON file is not an object."

            # Validate gender values when present (allow legacy files without gender)
            VALID_GENDERS = {None, "m", "f", "e"}
            for word, entry in new_data.items():
                for lex in entry.get("lexemes", []):
                    g = lex.get("gender", None)   # absent = legacy, treat as None
                    if g not in VALID_GENDERS:
                        return (
                            False,
                            f"Invalid gender value '{g}' for word '{word}'. "
                            "Expected: 'm', 'f', 'e' or null."
                        )

            before = len(self._data)
            for word, entry in new_data.items():
                if word not in self._data:
                    self._data[word] = entry

            added = len(self._data) - before
            self._save()
            return True, f"{added} word(s) imported, {len(new_data) - added} already present."

        except json.JSONDecodeError:
            return False, "Invalid or corrupted JSON file."
        except Exception as e:
            return False, f"Import error: {e}"