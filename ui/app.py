"""
ui/app.py
---------
Fenetre principale : configuration CustomTkinter, TabView, coordination
entre les trois onglets.
"""

import sys
import customtkinter as ctk
from PIL import Image, ImageTk
from pathlib import Path

from core import Dictionnaire, Lexique
from ui.tab_dictionnaire import TabDictionnaire
from ui.tab_lexique import TabLexique
from ui.tab_quiz import TabQuiz

# Dossier assets a la racine du projet
ASSETS_DIR = Path(__file__).parent.parent / "assets"

class App(ctk.CTk):
    """Fenetre principale de l'application Lexika."""

    TITRE      = "Lexika - French"
    LARGEUR_MIN = 860
    HAUTEUR_MIN = 600

    def __init__(self, db_path: str | Path, lexique_path: str | Path):
        super().__init__()

        # --- Configuration CustomTkinter ---
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Donnees ---
        self.dictionnaire = Dictionnaire(db_path)
        self.lexique = Lexique(lexique_path)

        # --- Fenetre ---
        self.title(self.TITRE)
        self.geometry("1060x700")
        self.minsize(self.LARGEUR_MIN, self.HAUTEUR_MIN)
        self.configure(fg_color="#12121C")

        # --- Icone (doit etre appliquee avant _construire_ui) ---
        self._appliquer_icone()

        self._construire_ui()
        self.protocol("WM_DELETE_WINDOW", self._quitter)

    # ------------------------------------------------------------------
    # Icone multiplateforme
    # ------------------------------------------------------------------

    def _appliquer_icone(self):
        """
        Applique l'icone de la fenetre selon la plateforme :
          - Windows  : assets/icon.ico
          - macOS    : assets/icon.icns
          - Linux    : assets/icon.png

        Si le fichier attendu est absent, tente un fallback sur .png.
        Echoue silencieusement si aucun fichier n'est disponible.
        """
        plateforme = sys.platform  # 'win32', 'darwin', 'linux'

        # Table de correspondance plateforme -> fichier prefere
        candidats: list[Path] = []

        if plateforme == "win32":
            candidats = [
                ASSETS_DIR / "icon.ico",
                ASSETS_DIR / "icon.png",   # fallback
            ]
        elif plateforme == "darwin":
            candidats = [
                ASSETS_DIR / "icon.icns",
                ASSETS_DIR / "icon.png",   # fallback
            ]
        else:
            # Linux et autres Unix
            candidats = [
                ASSETS_DIR / "icon.png",
                ASSETS_DIR / "icon.ico",   # fallback peu probable mais possible
            ]

        # Trouver le premier fichier existant
        icone = next((c for c in candidats if c.exists()), None)
        if icone is None:
            return  # aucun fichier disponible, on continue sans icone

        try:
            if plateforme == "win32" and icone.suffix == ".ico":
                # Windows : iconbitmap() gere nativement les .ico
                self.iconbitmap(str(icone))

            elif plateforme == "darwin" and icone.suffix == ".icns":
                # macOS : tkinter ne supporte pas icns directement,
                # on passe par Pillow -> PhotoImage
                self._icone_depuis_image(icone)

            else:
                # Linux (.png) et fallbacks
                self._icone_depuis_image(icone)

        except Exception:
            pass  # echec silencieux, l'icone n'est pas critique

    def _icone_depuis_image(self, chemin: Path):
        """
        Charge une image avec Pillow et l'applique comme icone via wm_iconphoto.
        Conserve une reference pour eviter le garbage collector.
        """
        img = Image.open(chemin)
        # wm_iconphoto fonctionne mieux avec des tailles standard
        img = img.resize((256, 256), Image.LANCZOS)
        self._icone_ref = ImageTk.PhotoImage(img)
        self.wm_iconphoto(True, self._icone_ref)

    # ------------------------------------------------------------------
    # Construction de l'interface
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
            text="Lexika - French",
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
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
            corner_radius=0,
            border_width=0
        )
        # CTkTabview ne supporte pas font= : on configure le bouton interne
        self._tabview._segmented_button.configure(
            font=ctk.CTkFont(family="Arial", size=14),
            height=44,
            dynamic_resizing=True
        )
        self._tabview.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 16))

        # Creation des trois onglets
        self._tabview.add("Dictionnaire")
        self._tabview.add("Lexique")
        self._tabview.add("Quiz")

        for nom in ["Dictionnaire", "Lexique", "Quiz"]:
            self._tabview._segmented_button._buttons_dict[nom].configure(
                width=280, height=44
            )
            self._tabview.tab(nom).grid_columnconfigure(0, weight=1)
            self._tabview.tab(nom).grid_rowconfigure(0, weight=1)

        # Instanciation des onglets
        self._tab_dico = TabDictionnaire(
            self._tabview.tab("Dictionnaire"),
            dictionnaire=self.dictionnaire,
            lexique=self.lexique,
        )
        self._tab_dico.grid(row=0, column=0, sticky="nsew")

        self._tab_lexique = TabLexique(
            self._tabview.tab("Lexique"),
            lexique=self.lexique,
            on_voir_dans_dico=self._naviguer_vers_dico,
        )
        self._tab_lexique.grid(row=0, column=0, sticky="nsew")

        self._tab_quiz = TabQuiz(
            self._tabview.tab("Quiz"),
            lexique=self.lexique,
        )
        self._tab_quiz.grid(row=0, column=0, sticky="nsew")

        # Rafraichissement croise a chaque changement d'onglet
        self._tabview.configure(command=self._on_changement_onglet)

    # ------------------------------------------------------------------
    # Coordination entre onglets
    # ------------------------------------------------------------------

    def _on_changement_onglet(self):
        """Synchronise les onglets dependants du lexique a chaque changement."""
        onglet = self._tabview.get()
        if "Lexique" in onglet:
            self._tab_lexique.rafraichir()
        elif "Quiz" in onglet:
            self._tab_quiz.rafraichir()

    def _naviguer_vers_dico(self, mot: str, entree: dict):
        """
        Callback appele depuis le lexique pour afficher un mot
        dans l'onglet Dictionnaire.
        """
        self._tab_dico.afficher_depuis_lexique(mot, entree)
        self._tabview.set("Dictionnaire")

    # ------------------------------------------------------------------
    # Fermeture propre
    # ------------------------------------------------------------------

    def _quitter(self):
        self.dictionnaire.fermer()
        self.destroy()