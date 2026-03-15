"""
ui/setup_window.py
------------------
Fenetre de premier lancement affichee si french_dict.db est absent.
Propose a l'utilisateur :
  - de telecharger le dictionnaire depuis Hugging Face
  - ou d'importer un fichier .db existant sur son disque

Lance l'application principale une fois le dictionnaire disponible.
"""

import shutil
import sqlite3
import threading
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox

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

# Colonnes minimales attendues dans la table 'mots'
COLONNES_REQUISES = {"forme", "pos", "definitions"}

# ---------------------------------------------------------------------------
# Validation du fichier .db
# ---------------------------------------------------------------------------

def _valider_db(chemin: Path) -> tuple[bool, str]:
    """
    Verifie qu'un fichier est bien un dictionnaire Lexika compatible.
    Retourne (valide: bool, message: str).
    """
    if chemin.suffix.lower() != ".db":
        return False, "Le fichier doit avoir l'extension .db"

    if chemin.stat().st_size < 1024:
        return False, "Fichier trop petit pour etre un dictionnaire valide."

    try:
        conn = sqlite3.connect(str(chemin))
        cursor = conn.cursor()

        # Verifier la presence de la table 'mots'
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mots'"
        )
        if not cursor.fetchone():
            conn.close()
            return False, "Table 'mots' introuvable — ce fichier n'est pas compatible."

        # Verifier les colonnes
        cursor.execute("PRAGMA table_info(mots)")
        colonnes = {row[1] for row in cursor.fetchall()}
        manquantes = COLONNES_REQUISES - colonnes
        if manquantes:
            conn.close()
            return (
                False,
                f"Colonnes manquantes : {', '.join(sorted(manquantes))}.\n"
                "Ce fichier n'est pas compatible avec Lexika."
            )

        # Verifier qu'il y a bien des données
        cursor.execute("SELECT COUNT(*) FROM mots")
        nb = cursor.fetchone()[0]
        conn.close()

        if nb == 0:
            return False, "La table 'mots' est vide."

        return True, f"Fichier valide — {nb:,} entrees trouvees."

    except sqlite3.DatabaseError:
        return False, "Fichier SQLite invalide ou corrompu."
    except Exception as e:
        return False, f"Erreur de validation : {e}"


# ---------------------------------------------------------------------------
# Fenetre principale de setup
# ---------------------------------------------------------------------------

class SetupWindow(ctk.CTk):
    """Fenetre de setup : telechargement ou import du dictionnaire."""

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Lexika - Installation")
        self.geometry("540x400")
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
            corner_radius=0, border_width=1, border_color="#2E2E42"
        )
        cadre.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        cadre.grid_columnconfigure(0, weight=1)

        # Titre
        ctk.CTkLabel(
            cadre,
            text="Dictionnaire introuvable",
            font=ctk.CTkFont(family="Georgia", size=20, weight="bold"),
            text_color=COULEUR_TEXTE,
        ).grid(row=0, column=0, pady=(24, 6))

        # Message
        ctk.CTkLabel(
            cadre,
            text="Le fichier french_dict.db est absent du dossier 'data'.\n"
                 "Telechargez-le ou importez-le depuis votre disque.",
            font=ctk.CTkFont(family="Georgia", size=13),
            text_color=COULEUR_NEUTRE,
            justify="center",
        ).grid(row=1, column=0, padx=24, pady=(0, 20))

        # Barre de progression (cachee par defaut)
        self._barre = ctk.CTkProgressBar(
            cadre,
            width=420,
            height=10,
            corner_radius=0,
            fg_color=COULEUR_SURFACE2,
            progress_color=COULEUR_ACCENT,
        )
        self._barre.set(0)
        self._barre.grid(row=2, column=0, padx=32, pady=(0, 6))
        self._barre.grid_remove()

        # Label de statut
        self._label_statut = ctk.CTkLabel(
            cadre,
            text="",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_NEUTRE,
            wraplength=460,
            justify="center",
        )
        self._label_statut.grid(row=3, column=0, padx=16, pady=(0, 16))

        # Separateur
        ctk.CTkFrame(
            cadre, height=1, fg_color="#2E2E42"
        ).grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 20))

        # --- Bloc Telecharger ---
        bloc_dl = ctk.CTkFrame(cadre, fg_color="transparent")
        bloc_dl.grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 10))
        bloc_dl.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bloc_dl,
            text="Depuis Internet (Hugging Face, ~270 Mo)",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_NEUTRE,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._btn_telecharger = ctk.CTkButton(
            bloc_dl,
            text="Telecharger",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            fg_color=COULEUR_ACCENT,
            hover_color="#3A8EEF",
            text_color="white",
            height=38, width=160, corner_radius=0,
            command=self._lancer_telechargement,
        )
        self._btn_telecharger.grid(row=0, column=1, padx=(12, 0))

        # --- Bloc Importer ---
        bloc_imp = ctk.CTkFrame(cadre, fg_color="transparent")
        bloc_imp.grid(row=6, column=0, sticky="ew", padx=24, pady=(0, 10))
        bloc_imp.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bloc_imp,
            text="Depuis disque (fichier .db compatible)",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_NEUTRE,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._btn_importer = ctk.CTkButton(
            bloc_imp,
            text="Importer",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            fg_color="#5A4E8A",
            hover_color="#6A5E9A",
            text_color="white",
            height=38, width=160, corner_radius=0,
            command=self._importer_db,
        )
        self._btn_importer.grid(row=0, column=1, padx=(12, 0))

        # --- Bouton Quitter ---
        self._btn_quitter = ctk.CTkButton(
            cadre,
            text="Quitter",
            font=ctk.CTkFont(family="Georgia", size=12),
            fg_color="transparent",
            hover_color="#2A2A3E",
            text_color=COULEUR_NEUTRE,
            height=30, corner_radius=0,
            command=self.destroy,
        )
        self._btn_quitter.grid(row=7, column=0, pady=(4, 20))

    # ------------------------------------------------------------------
    # Import depuis le disque
    # ------------------------------------------------------------------

    def _importer_db(self):
        chemin = filedialog.askopenfilename(
            title="Selectionner le fichier dictionnaire",
            filetypes=[("Base SQLite", "*.db"), ("Tous les fichiers", "*.*")],
        )
        if not chemin:
            return

        chemin = Path(chemin)
        self._label_statut.configure(
            text="Verification du fichier...", text_color=COULEUR_NEUTRE
        )
        self.update_idletasks()

        valide, message = _valider_db(chemin)

        if not valide:
            self._label_statut.configure(
                text=f"Fichier invalide : {message}", text_color=COULEUR_ERREUR
            )
            return

        # Copie vers data/
        try:
            DB_DEST.parent.mkdir(parents=True, exist_ok=True)
            self._label_statut.configure(
                text="Copie en cours...", text_color=COULEUR_NEUTRE
            )
            self.update_idletasks()
            shutil.copy2(chemin, DB_DEST)
        except Exception as e:
            self._label_statut.configure(
                text=f"Erreur lors de la copie : {e}", text_color=COULEUR_ERREUR
            )
            return

        self._label_statut.configure(
            text=f"OK  {message}", text_color=COULEUR_SUCCES
        )
        self._btn_importer.configure(
            state="disabled", text="OK  Importe", fg_color=COULEUR_SUCCES
        )
        self._btn_telecharger.configure(state="disabled")
        self._btn_quitter.configure(state="disabled")
        self.after(1400, self._lancer_app)

    # ------------------------------------------------------------------
    # Telechargement depuis Hugging Face
    # ------------------------------------------------------------------

    def _lancer_telechargement(self):
        if self._telechargement_en_cours:
            return

        self._telechargement_en_cours = True
        self._btn_telecharger.configure(state="disabled", text="Telechargement...")
        self._btn_importer.configure(state="disabled")
        self._btn_quitter.configure(state="disabled")
        self._barre.grid()
        self._barre.configure(mode="indeterminate")
        self._barre.start()
        self._label_statut.configure(
            text="Connexion a Hugging Face...", text_color=COULEUR_NEUTRE
        )

        thread = threading.Thread(target=self._telecharger, daemon=True)
        thread.start()

    def _telecharger(self):
        """Telechargement dans un thread separe pour ne pas bloquer l'UI."""
        try:
            DB_DEST.parent.mkdir(parents=True, exist_ok=True)
            tmp = DB_DEST.with_suffix(".tmp")

            def hook(compte, taille_bloc, taille_totale):
                if taille_totale > 0:
                    telecharges = compte * taille_bloc
                    progression = min(telecharges / taille_totale, 1.0)
                    mo_dl  = telecharges    / 1_048_576
                    mo_tot = taille_totale  / 1_048_576
                    self.after(0, self._maj_progression, progression, mo_dl, mo_tot)

            urllib.request.urlretrieve(DB_URL, tmp, reporthook=hook)
            tmp.rename(DB_DEST)
            self.after(0, self._telechargement_reussi)

        except Exception as e:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            self.after(0, self._telechargement_echoue, str(e))

    def _maj_progression(self, progression: float, mo_dl: float, mo_tot: float):
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
            text="Telechargement termine - lancement de Lexika...",
            text_color=COULEUR_SUCCES,
        )
        self._btn_telecharger.configure(
            text="OK  Termine", fg_color=COULEUR_SUCCES, hover_color=COULEUR_SUCCES
        )
        self.after(1200, self._lancer_app)

    def _telechargement_echoue(self, erreur: str):
        self._telechargement_en_cours = False
        self._barre.stop()
        self._barre.set(0)
        msg = erreur[:70] + "..." if len(erreur) > 70 else erreur
        self._label_statut.configure(
            text=f"Erreur : {msg}", text_color=COULEUR_ERREUR
        )
        self._btn_telecharger.configure(
            state="normal", text="Reessayer",
            fg_color=COULEUR_ERREUR, hover_color="#CC4444"
        )
        self._btn_importer.configure(state="normal")
        self._btn_quitter.configure(state="normal")

    # ------------------------------------------------------------------
    # Lancement de l'application
    # ------------------------------------------------------------------

    def _lancer_app(self):
        self.destroy()
        from ui.app import App
        app = App(
            db_path=DB_DEST,
            lexique_path=DB_DEST.parent / "lexique.json"
        )
        app.mainloop()