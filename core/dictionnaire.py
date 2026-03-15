"""
core/dictionnaire.py
--------------------
Interface entre l'application et la base SQLite du dictionnaire.
Toutes les requetes SQL sont centralisees ici.
"""

import json
import sqlite3
import difflib
import unicodedata
from pathlib import Path
from typing import Optional

def _normaliser(texte: str) -> str:
    """Supprime les accents d'une chaine pour la comparaison."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texte)
        if unicodedata.category(c) != 'Mn'
    )

_VARIANTES_ACCENTS = {
    'a': 'àâä',
    'e': 'éèêë',
    'i': 'îï',
    'o': 'ôöœ',
    'u': 'ùûü',
    'c': 'ç',
}

class Dictionnaire:

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Base de donnees introuvable : {self.db_path}"
            )
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def rechercher(self, mot: str) -> Optional[list[dict]]:
        mot = mot.strip().lower()
        if not mot:
            return None
        cursor = self._conn.cursor()
        cursor.execute("SELECT pos, definitions FROM mots WHERE forme = ?", (mot,))
        rows = cursor.fetchall()
        if not rows:
            return None
        return [{"pos": row["pos"], "definitions": json.loads(row["definitions"])} for row in rows]

    def suggerer(self, mot: str, n: int = 8) -> list[str]:
        mot = mot.strip().lower()
        if not mot:
            return []

        mot_norm = _normaliser(mot)
        cursor = self._conn.cursor()

        # Passe 1 : prefixes avec variantes accentuees (requetes indexees)
        prefixes = self._prefixes_avec_variantes(mot_norm, longueur=3)
        placeholders = " OR ".join(["forme LIKE ?"] * len(prefixes))
        params = [f"{p}%" for p in prefixes]
        cursor.execute(f"SELECT DISTINCT forme FROM mots WHERE {placeholders} LIMIT 600", params)
        candidats = [row["forme"] for row in cursor.fetchall()]

        # Passe 2 : complementer si peu de resultats
        if len(candidats) < 20 and len(mot_norm) >= 2:
            prefixes2 = self._prefixes_avec_variantes(mot_norm[1:], longueur=2)
            ph2 = " OR ".join(["forme LIKE ?"] * len(prefixes2))
            params2 = [f"%{p}%" for p in prefixes2]
            cursor.execute(f"SELECT DISTINCT forme FROM mots WHERE {ph2} LIMIT 300", params2)
            vus = set(candidats)
            for row in cursor.fetchall():
                if row["forme"] not in vus:
                    candidats.append(row["forme"])
                    vus.add(row["forme"])

        if not candidats:
            return []

        # Passe 3 : tri par similarite sur formes normalisees
        norm_vers_orig: dict[str, str] = {}
        for c in candidats:
            c_norm = _normaliser(c)
            if c_norm not in norm_vers_orig:
                norm_vers_orig[c_norm] = c

        proches_norm = difflib.get_close_matches(
            mot_norm, list(norm_vers_orig.keys()), n=n * 2, cutoff=0.65
        )

        resultats = [norm_vers_orig[p] for p in proches_norm if p in norm_vers_orig]

        if not resultats and candidats:
            resultats = candidats[:n]

        return resultats[:n]

    def _prefixes_avec_variantes(self, base: str, longueur: int) -> list[str]:
        prefixe = base[:longueur]
        variantes: set[str] = {prefixe}
        for i, lettre in enumerate(prefixe):
            if lettre in _VARIANTES_ACCENTS:
                for lettre_acc in _VARIANTES_ACCENTS[lettre]:
                    variantes.add(prefixe[:i] + lettre_acc + prefixe[i + 1:])
        return list(variantes)

    def forme_existe(self, mot: str) -> bool:
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM mots WHERE forme = ? LIMIT 1", (mot.strip().lower(),))
        return cursor.fetchone() is not None

    def fermer(self):
        if self._conn:
            self._conn.close()

    def __del__(self):
        try:
            self.fermer()
        except Exception:
            pass
