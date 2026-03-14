"""
ui/setup_window.py
------------------
Fenêtre de premier lancement affichée si french_dict.db est absent.
Propose à l'utilisateur de télécharger le dictionnaire depuis Hugging Face.
Lance l'application principale une fois le téléchargement terminé.
"""

import threading
import urllib.request
from pathlib import Path

import customtkinter as ctk

DB_URL  = "https://huggingface.co/datasets/Kartmaan/french-dictionary/resolve/main/french_dict.db"
DB_DEST = Path(__file__).parent.parent / "data" / "french_dict.db"

COULEUR_BG       = "#12121C"
COULEUR_SURFACE  = "#1E1E2E"
COULEUR_SURFACE2 = "#2A2A3E"
COULEUR_ACCENT   = "#4A9EFF"
COULEUR_SUCCES   = "#3DBE7A"
COULEUR_ERREUR   = "#FF5F5F"
COULEUR_TEXTE    = "#E8E8F0"
COULEUR_NEUTRE   = "#8A8A9A"


class SetupWindow(ctk.CTk):
    """Fenêtre de setup : téléchargement du dictionnaire au premier lancement."""

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Lexika — Installation")
        self.geometry("520x360")
        self.resizable(False, False)
        self.configure(fg_color=COULEUR_BG)

        self._telechargement_en_cours = False
        self._construire_ui()

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    def _construire_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        cadre = ctk.CTkFrame(
            self, fg_color=COULEUR_SURFACE,
            corner_radius=16, border_width=1, border_color="#2E2E42"
        )
        cadre.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        cadre.grid_columnconfigure(0, weight=1)

        # Icône
        ctk.CTkLabel(
            cadre,
            text="📚",
            font=ctk.CTkFont(size=48),
        ).grid(row=0, column=0, pady=(28, 4))

        # Titre
        ctk.CTkLabel(
            cadre,
            text="Dictionnaire introuvable",
            font=ctk.CTkFont(family="Georgia", size=20, weight="bold"),
            text_color=COULEUR_TEXTE,
        ).grid(row=1, column=0, pady=(0, 8))

        # Message
        ctk.CTkLabel(
            cadre,
            text="Le fichier french_dict.db est absent du dossier data/.\n"
                 "Voulez-vous le télécharger maintenant ? (≈ 270 Mo)",
            font=ctk.CTkFont(family="Georgia", size=13),
            text_color=COULEUR_NEUTRE,
            justify="center",
        ).grid(row=2, column=0, padx=24, pady=(0, 20))

        # Barre de progression (cachée par défaut)
        self._barre = ctk.CTkProgressBar(
            cadre,
            width=380,
            height=10,
            corner_radius=5,
            fg_color=COULEUR_SURFACE2,
            progress_color=COULEUR_ACCENT,
        )
        self._barre.set(0)
        self._barre.grid(row=3, column=0, padx=32, pady=(0, 8))
        self._barre.grid_remove()  # caché initialement

        # Label de statut
        self._label_statut = ctk.CTkLabel(
            cadre,
            text="",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_NEUTRE,
        )
        self._label_statut.grid(row=4, column=0, pady=(0, 16))

        # Boutons
        btns = ctk.CTkFrame(cadre, fg_color="transparent")
        btns.grid(row=5, column=0, pady=(0, 28))

        self._btn_annuler = ctk.CTkButton(
            btns,
            text="Quitter",
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color=COULEUR_SURFACE2,
            hover_color="#3A3A5C",
            text_color=COULEUR_TEXTE,
            height=40, width=120, corner_radius=8,
            command=self.destroy,
        )
        self._btn_annuler.pack(side="left", padx=(0, 12))

        self._btn_telecharger = ctk.CTkButton(
            btns,
            text="⬇  Télécharger",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            fg_color=COULEUR_ACCENT,
            hover_color="#3A8EEF",
            text_color="white",
            height=40, width=160, corner_radius=8,
            command=self._lancer_telechargement,
        )
        self._btn_telecharger.pack(side="left")

    # ------------------------------------------------------------------
    # Téléchargement
    # ------------------------------------------------------------------

    def _lancer_telechargement(self):
        if self._telechargement_en_cours:
            return

        self._telechargement_en_cours = True
        self._btn_telecharger.configure(state="disabled", text="Téléchargement…")
        self._btn_annuler.configure(state="disabled")
        self._barre.grid()
        self._barre.configure(mode="indeterminate")
        self._barre.start()
        self._label_statut.configure(
            text="Connexion à Hugging Face…", text_color=COULEUR_NEUTRE
        )

        thread = threading.Thread(target=self._telecharger, daemon=True)
        thread.start()

    def _telecharger(self):
        """Téléchargement dans un thread séparé pour ne pas bloquer l'UI."""
        try:
            DB_DEST.parent.mkdir(parents=True, exist_ok=True)
            tmp = DB_DEST.with_suffix(".tmp")

            total_octets = [0]
            telecharges  = [0]

            # Récupérer la taille totale via HEAD
            with urllib.request.urlopen(DB_URL) as resp:
                content_length = resp.headers.get("Content-Length")
                if content_length:
                    total_octets[0] = int(content_length)

            def hook(compte, taille_bloc, taille_totale):
                if taille_totale > 0:
                    telecharges[0] = compte * taille_bloc
                    progression = min(telecharges[0] / taille_totale, 1.0)
                    mo_dl  = telecharges[0] / 1_048_576
                    mo_tot = taille_totale  / 1_048_576
                    self.after(0, self._maj_progression, progression, mo_dl, mo_tot)

            urllib.request.urlretrieve(DB_URL, tmp, reporthook=hook)
            tmp.rename(DB_DEST)
            self.after(0, self._telechargement_reussi)

        except Exception as e:
            if 'tmp' in dir() and tmp.exists():
                tmp.unlink(missing_ok=True)
            self.after(0, self._telechargement_echoue, str(e))

    def _maj_progression(self, progression: float, mo_dl: float, mo_tot: float):
        """Mise à jour de la barre depuis le thread principal."""
        self._barre.stop()
        self._barre.configure(mode="determinate")
        self._barre.set(progression)
        self._label_statut.configure(
            text=f"{mo_dl:.1f} Mo / {mo_tot:.1f} Mo  ({progression*100:.0f}%)",
            text_color=COULEUR_NEUTRE,
        )

    def _telechargement_reussi(self):
        self._barre.set(1.0)
        self._label_statut.configure(
            text="✓  Téléchargement terminé — lancement de Lexika…",
            text_color=COULEUR_SUCCES,
        )
        self._btn_telecharger.configure(
            text="✓  Terminé", fg_color=COULEUR_SUCCES, hover_color=COULEUR_SUCCES
        )
        # Lancer l'app principale après un court délai
        self.after(1200, self._lancer_app)

    def _telechargement_echoue(self, erreur: str):
        self._telechargement_en_cours = False
        self._barre.stop()
        self._barre.set(0)
        self._label_statut.configure(
            text=f"Erreur : {erreur[:60]}…" if len(erreur) > 60 else f"Erreur : {erreur}",
            text_color=COULEUR_ERREUR,
        )
        self._btn_telecharger.configure(
            state="normal", text="↺  Réessayer",
            fg_color=COULEUR_ERREUR, hover_color="#CC4444"
        )
        self._btn_annuler.configure(state="normal")

    def _lancer_app(self):
        """Ferme la fenêtre de setup et lance l'application principale."""
        self.destroy()
        # Instanciation ici pour éviter les imports circulaires
        from ui.app import App
        app = App(db_path=DB_DEST,
                  lexique_path=DB_DEST.parent / "lexique.json")
        app.mainloop()
