"""
core/dictionnaire.py
--------------------
Interface entre l'application et la base SQLite du dictionnaire.
Toutes les requêtes SQL sont centralisées ici.
"""

import json
import sqlite3
import difflib
from pathlib import Path
from typing import Optional


class Dictionnaire:
    """
    Gère l'accès en lecture à la base SQLite du dictionnaire français.
    
    Schéma attendu :
        TABLE mots (id, forme TEXT, pos TEXT, definitions TEXT)
        INDEX idx_forme ON mots(forme)
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Base de données introuvable : {self.db_path}\n"
                "Veuillez placer french_dict.db dans le dossier data/."
            )
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,   # nécessaire pour CTk (thread UI)
        )
        self._conn.row_factory = sqlite3.Row

    # ------------------------------------------------------------------
    # Recherche exacte
    # ------------------------------------------------------------------

    def rechercher(self, mot: str) -> Optional[list[dict]]:
        """
        Retourne la liste des lexèmes pour un mot exact, ou None si introuvable.

        Chaque élément de la liste est un dict :
            { "pos": "N", "definitions": [ {...}, ... ] }
        """
        mot = mot.strip().lower()
        if not mot:
            return None

        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT pos, definitions FROM mots WHERE forme = ?",
            (mot,)
        )
        rows = cursor.fetchall()
        if not rows:
            return None

        return [
            {
                "pos": row["pos"],
                "definitions": json.loads(row["definitions"]),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Suggestions de mots proches
    # ------------------------------------------------------------------

    def suggerer(self, mot: str, n: int = 8) -> list[str]:
        """
        Retourne jusqu'à n mots proches de la saisie utilisateur.
        
        Stratégie en deux passes :
          1. Requête LIKE sur le préfixe → candidats rapides
          2. difflib.get_close_matches sur les candidats → tri par similarité
        """
        mot = mot.strip().lower()
        if not mot:
            return []

        cursor = self._conn.cursor()

        # Passe 1 : candidats par préfixe (rapide, indexé)
        prefix = mot[:3] if len(mot) >= 3 else mot
        cursor.execute(
            "SELECT DISTINCT forme FROM mots WHERE forme LIKE ? LIMIT 300",
            (f"{prefix}%",)
        )
        candidats = [row["forme"] for row in cursor.fetchall()]

        # Passe 2 : compléter si peu de résultats préfixe
        if len(candidats) < 20:
            cursor.execute(
                "SELECT DISTINCT forme FROM mots WHERE forme LIKE ? LIMIT 200",
                (f"%{mot[1:]}%",)
            )
            extra = [row["forme"] for row in cursor.fetchall()]
            candidats = list(dict.fromkeys(candidats + extra))  # dédoublonnage

        # Tri par similarité
        proches = difflib.get_close_matches(
            mot, candidats, n=n, cutoff=0.6
        )

        # Fallback : si difflib ne trouve rien, renvoyer les premiers candidats
        if not proches and candidats:
            proches = candidats[:n]

        return proches

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def forme_existe(self, mot: str) -> bool:
        """Vérifie rapidement si une forme est présente dans le dictionnaire."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT 1 FROM mots WHERE forme = ? LIMIT 1",
            (mot.strip().lower(),)
        )
        return cursor.fetchone() is not None

    def fermer(self):
        """Ferme la connexion SQLite proprement."""
        if self._conn:
            self._conn.close()

    def __del__(self):
        try:
            self.fermer()
        except Exception:
            pass
