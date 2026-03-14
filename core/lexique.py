"""
core/lexique.py
---------------
Gestion complète du lexique personnel (favoris).
Stockage dans un fichier JSON local.

Format du fichier lexique.json :
{
    "mot": {
        "source": "dictionnaire" | "personnalisé",
        "lexemes": [
            {
                "pos": "N",
                "definitions": [
                    {
                        "gloss": "...",
                        "register": null,
                        "semantic": null,
                        "domain": null,
                        "exemples": [],
                        "sous_definitions": []
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


class Lexique:
    """
    Gère le lexique personnel de l'utilisateur.
    Toutes les modifications sont immédiatement persistées sur disque.
    """

    def __init__(self, json_path: str | Path):
        self.json_path = Path(json_path)
        self._data: dict = {}
        self._charger()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _charger(self):
        """Charge le fichier JSON, crée un lexique vide si inexistant."""
        if self.json_path.exists():
            with open(self.json_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
            self._sauvegarder()

    def _sauvegarder(self):
        """Persiste les données sur disque."""
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def mots(self) -> list[str]:
        """Retourne la liste des mots triés alphabétiquement."""
        return sorted(self._data.keys(), key=lambda m: m.lower())

    def contient(self, mot: str) -> bool:
        """Vérifie si un mot est déjà dans le lexique."""
        return mot.strip().lower() in self._data

    def obtenir(self, mot: str) -> Optional[dict]:
        """Retourne l'entrée complète d'un mot, ou None si absent."""
        return self._data.get(mot.strip().lower())

    def est_vide(self) -> bool:
        return len(self._data) == 0

    def nombre_mots(self) -> int:
        return len(self._data)

    # ------------------------------------------------------------------
    # Écriture
    # ------------------------------------------------------------------

    def ajouter_depuis_dictionnaire(self, mot: str, lexemes: list[dict]) -> bool:
        """
        Ajoute un mot provenant du dictionnaire.
        Retourne False si le mot est déjà présent.
        """
        cle = mot.strip().lower()
        if cle in self._data:
            return False
        self._data[cle] = {
            "source": "dictionnaire",
            "lexemes": lexemes,
        }
        self._sauvegarder()
        return True

    def ajouter_personnalise(self, mot: str, definitions: list[str]) -> bool:
        """
        Ajoute un mot personnalisé saisi par l'utilisateur.
        definitions : liste de chaînes (une par définition).
        Retourne False si le mot est déjà présent.
        """
        cle = mot.strip().lower()
        if cle in self._data:
            return False

        lexemes = [
            {
                "pos": "?",
                "definitions": [
                    {
                        "gloss": d.strip(),
                        "register": None,
                        "semantic": None,
                        "domain": None,
                        "exemples": [],
                        "sous_definitions": [],
                    }
                    for d in definitions
                    if d.strip()
                ],
            }
        ]
        self._data[cle] = {
            "source": "personnalisé",
            "lexemes": lexemes,
        }
        self._sauvegarder()
        return True

    def supprimer(self, mot: str) -> bool:
        """
        Supprime un mot du lexique.
        Retourne False si le mot était absent.
        """
        cle = mot.strip().lower()
        if cle not in self._data:
            return False
        del self._data[cle]
        self._sauvegarder()
        return True

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def exporter(self, chemin: str | Path) -> bool:
        """
        Exporte le lexique vers un fichier JSON choisi par l'utilisateur.
        Retourne True si succès.
        """
        try:
            chemin = Path(chemin)
            chemin.parent.mkdir(parents=True, exist_ok=True)
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def importer(self, chemin: str | Path) -> tuple[bool, str]:
        """
        Importe un lexique depuis un fichier JSON.
        Les mots existants sont conservés ; les nouveaux sont fusionnés.
        Retourne (succès: bool, message: str).
        """
        try:
            chemin = Path(chemin)
            with open(chemin, "r", encoding="utf-8") as f:
                nouveau = json.load(f)

            if not isinstance(nouveau, dict):
                return False, "Format invalide : le fichier JSON n'est pas un objet."

            avant = len(self._data)
            for mot, entree in nouveau.items():
                if mot not in self._data:
                    self._data[mot] = entree

            ajoutes = len(self._data) - avant
            self._sauvegarder()
            return True, f"{ajoutes} mot(s) importé(s), {len(nouveau) - ajoutes} déjà présent(s)."

        except json.JSONDecodeError:
            return False, "Fichier JSON invalide ou corrompu."
        except Exception as e:
            return False, f"Erreur lors de l'import : {e}"
