"""
ui/app.py
---------
Fenêtre principale : configuration CustomTkinter, TabView, coordination
entre les trois onglets.
"""

import customtkinter as ctk
from pathlib import Path

from core import Dictionnaire, Lexique
from ui.tab_dictionnaire import TabDictionnaire
from ui.tab_lexique import TabLexique
from ui.tab_quiz import TabQuiz


class App(ctk.CTk):
    """Fenêtre principale de l'application French Dict."""

    TITRE = "French Dict"
    LARGEUR_MIN = 860
    HAUTEUR_MIN = 600

    def __init__(self, db_path: str | Path, lexique_path: str | Path):
        super().__init__()

        # --- Configuration CustomTkinter ---
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Données ---
        self.dictionnaire = Dictionnaire(db_path)
        self.lexique = Lexique(lexique_path)

        # --- Fenêtre ---
        self.title(self.TITRE)
        self.geometry("1060x700")
        self.minsize(self.LARGEUR_MIN, self.HAUTEUR_MIN)
        self.configure(fg_color="#12121C")

        self._construire_ui()
        self.protocol("WM_DELETE_WINDOW", self._quitter)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _construire_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Bandeau titre
        bandeau = ctk.CTkFrame(self, fg_color="#1A1A2E", corner_radius=0, height=52)
        bandeau.grid(row=0, column=0, sticky="ew")
        bandeau.grid_propagate(False)
        bandeau.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bandeau,
            text="✦  French Dict",
            font=ctk.CTkFont(family="Georgia", size=20, weight="bold"),
            text_color="#E8E8F0",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=10)

        # TabView principal
        self._tabview = ctk.CTkTabview(
            self,
            fg_color="#1E1E2E",
            segmented_button_fg_color="#1A1A2E",
            segmented_button_selected_color="#4A9EFF",
            segmented_button_selected_hover_color="#3A8EEF",
            segmented_button_unselected_color="#1A1A2E",
            segmented_button_unselected_hover_color="#2A2A3E",
            text_color="#E8E8F0",
            text_color_disabled="#5A5A6A",
            corner_radius=12,
            border_width=0,
        )
        self._tabview.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 16))

        # Création des trois onglets
        self._tabview.add("📖  Dictionnaire")
        self._tabview.add("📚  Lexique")
        self._tabview.add("🧠  Quiz")

        for nom in ["📖  Dictionnaire", "📚  Lexique", "🧠  Quiz"]:
            self._tabview.tab(nom).grid_columnconfigure(0, weight=1)
            self._tabview.tab(nom).grid_rowconfigure(0, weight=1)

        # Instanciation des onglets
        self._tab_dico = TabDictionnaire(
            self._tabview.tab("📖  Dictionnaire"),
            dictionnaire=self.dictionnaire,
            lexique=self.lexique,
        )
        self._tab_dico.grid(row=0, column=0, sticky="nsew")

        self._tab_lexique = TabLexique(
            self._tabview.tab("📚  Lexique"),
            lexique=self.lexique,
            on_voir_dans_dico=self._naviguer_vers_dico,
        )
        self._tab_lexique.grid(row=0, column=0, sticky="nsew")

        self._tab_quiz = TabQuiz(
            self._tabview.tab("🧠  Quiz"),
            lexique=self.lexique,
        )
        self._tab_quiz.grid(row=0, column=0, sticky="nsew")

        # Rafraîchissement croisé à chaque changement d'onglet
        self._tabview.configure(command=self._on_changement_onglet)

    # ------------------------------------------------------------------
    # Coordination entre onglets
    # ------------------------------------------------------------------

    def _on_changement_onglet(self):
        """Synchronise les onglets dépendants du lexique à chaque changement."""
        onglet = self._tabview.get()
        if "Lexique" in onglet:
            self._tab_lexique.rafraichir()
        elif "Quiz" in onglet:
            self._tab_quiz.rafraichir()

    def _naviguer_vers_dico(self, mot: str, entree: dict):
        """
        Callback appelé depuis le lexique pour afficher un mot
        dans l'onglet Dictionnaire.
        """
        self._tab_dico.afficher_depuis_lexique(mot, entree)
        self._tabview.set("📖  Dictionnaire")

    # ------------------------------------------------------------------
    # Fermeture propre
    # ------------------------------------------------------------------

    def _quitter(self):
        self.dictionnaire.fermer()
        self.destroy()
