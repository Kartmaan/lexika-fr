"""
ui/tab_quiz.py
--------------
Onglet Quiz : carte mot/définition avec changement de couleur, suivi de session.
"""

import random
import customtkinter as ctk

COULEUR_SURFACE   = "#1E1E2E"
COULEUR_SURFACE2  = "#2A2A3E"
COULEUR_TEXTE     = "#E8E8F0"
COULEUR_TEXTE2    = "#A0A0B8"
COULEUR_NEUTRE    = "#8A8A9A"
COULEUR_ACCENT    = "#4A9EFF"

# Couleurs des deux faces de la carte
COULEUR_CARTE_MOT  = "#1A2A4A"   # face "mot"  → bleu sombre
COULEUR_CARTE_DEF  = "#1A3A2A"   # face "def"  → vert sombre
BORDER_CARTE_MOT   = "#3A5A8A"
BORDER_CARTE_DEF   = "#3A7A5A"

POS_LABELS = {
    "N": "Nom", "V": "Verbe", "ADJ": "Adjectif", "ADV": "Adverbe",
    "PRO": "Pronom", "DET": "Déterminant", "PRE": "Préposition",
    "CON": "Conjonction", "INT": "Interjection", "?": "Indéfini",
}


class TabQuiz(ctk.CTkFrame):
    """Onglet Quiz de vocabulaire."""

    def __init__(self, parent, lexique, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.lexique = lexique

        self._mots_session: list[str] = []   # mots restants dans la session
        self._mots_vus: list[str] = []       # mots déjà parcourus
        self._mot_courant: str | None = None
        self._face_mot: bool = True          # True = face mot, False = face def

        self._construire_ui()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _construire_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # En-tête
        entete = ctk.CTkFrame(self, fg_color=COULEUR_SURFACE, corner_radius=0)
        entete.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            entete,
            text="Quiz de vocabulaire",
            font=ctk.CTkFont(family="Georgia", size=18, weight="bold"),
            text_color=COULEUR_TEXTE,
        ).pack(side="left", padx=16, pady=12)

        self._label_progression = ctk.CTkLabel(
            entete,
            text="",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_NEUTRE,
        )
        self._label_progression.pack(side="left", padx=4, pady=12)

        self._btn_recommencer = ctk.CTkButton(
            entete,
            text="↺  Recommencer",
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color=COULEUR_SURFACE2,
            hover_color="#3A3A5C",
            text_color=COULEUR_ACCENT,
            height=34, corner_radius=0,
            command=self._demarrer_session,
        )
        self._btn_recommencer.pack(side="right", padx=12, pady=10)

        # Zone centrale (carte + boutons)
        self._zone_centrale = ctk.CTkFrame(
            self, fg_color="transparent"
        )
        self._zone_centrale.grid(row=1, column=0, sticky="nsew",
                                  padx=20, pady=(0, 20))
        self._zone_centrale.grid_columnconfigure(0, weight=1)
        self._zone_centrale.grid_rowconfigure(0, weight=1)

        self._afficher_ecran_attente()

    # ------------------------------------------------------------------
    # Écrans
    # ------------------------------------------------------------------

    def _vider_zone(self):
        for w in self._zone_centrale.winfo_children():
            w.destroy()

    def _afficher_ecran_attente(self):
        """Écran quand le lexique est vide ou avant de démarrer."""
        self._vider_zone()

        cadre = ctk.CTkFrame(
            self._zone_centrale,
            fg_color=COULEUR_SURFACE,
            corner_radius=0,
        )
        cadre.grid(row=0, column=0)

        vide = self.lexique.est_vide()

        ctk.CTkLabel(
            cadre,
            text="?",
            font=ctk.CTkFont(size=48),
            text_color=COULEUR_TEXTE,
        ).pack(pady=(32, 8), padx=48)

        msg = (
            "Votre lexique est vide.\nAjoutez des mots depuis l'onglet Dictionnaire."
            if vide else
            f"Prêt à réviser ?\n{self.lexique.nombre_mots()} mot(s) disponible(s)."
        )
        ctk.CTkLabel(
            cadre,
            text=msg,
            font=ctk.CTkFont(family="Georgia", size=15),
            text_color=COULEUR_TEXTE2,
            justify="center",
        ).pack(pady=(0, 16), padx=48)

        if not vide:
            ctk.CTkButton(
                cadre,
                text="Commencer le quiz",
                font=ctk.CTkFont(family="Georgia", size=15, weight="bold"),
                fg_color=COULEUR_ACCENT,
                hover_color="#3A8EEF",
                text_color="white",
                height=44, width=200, corner_radius=0,
                command=self._demarrer_session,
            ).pack(pady=(0, 32))

    def _afficher_fin_session(self):
        """Écran affiché quand tous les mots ont été parcourus."""
        self._vider_zone()
        self._label_progression.configure(text="")

        cadre = ctk.CTkFrame(
            self._zone_centrale,
            fg_color=COULEUR_SURFACE,
            corner_radius=0,
        )
        cadre.grid(row=0, column=0)

        ctk.CTkLabel(
            cadre,
            text="Bravo !",
            font=ctk.CTkFont(size=48),
        ).pack(pady=(32, 8), padx=64)

        ctk.CTkLabel(
            cadre,
            text=f"Bravo ! Vous avez parcouru\nles {len(self._mots_vus)} mots du lexique.",
            font=ctk.CTkFont(family="Georgia", size=15),
            text_color=COULEUR_TEXTE,
            justify="center",
        ).pack(pady=(0, 16))

        ctk.CTkButton(
            cadre,
            text="↺  Rejouer",
            font=ctk.CTkFont(family="Georgia", size=15, weight="bold"),
            fg_color=COULEUR_ACCENT,
            hover_color="#3A8EEF",
            text_color="white",
            height=44, width=160, corner_radius=0,
            command=self._demarrer_session,
        ).pack(pady=(0, 32))

    def _afficher_carte(self):
        """Affiche la carte du mot courant."""
        self._vider_zone()

        entree = self.lexique.obtenir(self._mot_courant)
        if not entree:
            self._mot_suivant()
            return

        # Wrapper centré verticalement
        wrapper = ctk.CTkFrame(self._zone_centrale, fg_color="transparent")
        wrapper.grid(row=0, column=0)
        wrapper.grid_columnconfigure(0, weight=1)

        # --- Carte ---
        couleur_carte = COULEUR_CARTE_MOT if self._face_mot else COULEUR_CARTE_DEF
        border_carte  = BORDER_CARTE_MOT  if self._face_mot else BORDER_CARTE_DEF

        self._carte = ctk.CTkFrame(
            wrapper,
            fg_color=couleur_carte,
            corner_radius=0,
            border_width=2,
            border_color=border_carte,
            width=560,
        )
        self._carte.grid(row=0, column=0, pady=(0, 24))
        self._carte.grid_columnconfigure(0, weight=1)

        if self._face_mot:
            self._construire_face_mot(self._carte)
        else:
            self._construire_face_def(self._carte, entree)

        # --- Bouton "Mot suivant" ---
        self._btn_suivant = ctk.CTkButton(
            wrapper,
            text="Mot suivant  →",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color=COULEUR_SURFACE,
            hover_color="#3A3A5C",
            border_color="#3A3A5C",
            border_width=1,
            text_color=COULEUR_TEXTE,
            height=42, width=200, corner_radius=0,
            command=self._mot_suivant,
        )
        self._btn_suivant.grid(row=1, column=0)

    def _construire_face_mot(self, parent):
        """Face avant : affiche le mot et bouton 'Voir la réponse'."""
        ctk.CTkLabel(
            parent,
            text="Quelle est la définition de…",
            font=ctk.CTkFont(family="Georgia", size=13, slant="italic"),
            text_color="#7A9ABE",
        ).grid(row=0, column=0, pady=(28, 4), padx=40)

        ctk.CTkLabel(
            parent,
            text=self._mot_courant.capitalize(),
            font=ctk.CTkFont(family="Georgia", size=36, weight="bold"),
            text_color="#A8D0FF",
        ).grid(row=1, column=0, pady=(4, 28), padx=40)

        ctk.CTkButton(
            parent,
            text="Voir la réponse",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color="#2A4A7A",
            hover_color="#3A5A8A",
            text_color="#A8D0FF",
            height=40, width=180, corner_radius=0,
            command=self._retourner_carte,
        ).grid(row=2, column=0, pady=(0, 28))

    def _construire_face_def(self, parent, entree: dict):
        """Face arrière : affiche la/les définitions et bouton 'Voir le mot'."""
        ctk.CTkLabel(
            parent,
            text=self._mot_courant.capitalize(),
            font=ctk.CTkFont(family="Georgia", size=20, weight="bold"),
            text_color="#80C8A0",
        ).grid(row=0, column=0, pady=(24, 4), padx=40, sticky="w")

        # Séparateur
        ctk.CTkFrame(
            parent, height=1, fg_color="#3A7A5A"
        ).grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))

        # Définitions (limitées pour tenir sur la carte)
        row = 2
        for lexeme in entree.get("lexemes", []):
            pos = lexeme.get("pos", "?")
            pos_label = POS_LABELS.get(pos, pos)

            ctk.CTkLabel(
                parent,
                text=f"  {pos_label}  ",
                font=ctk.CTkFont(family="Georgia", size=10, weight="bold"),
                fg_color="#2A5A3A",
                text_color="#80C8A0",
                corner_radius=0,
                height=20,
            ).grid(row=row, column=0, sticky="w", padx=24, pady=(4, 2))
            row += 1

            for i, defn in enumerate(lexeme.get("definitions", [])[:3], 1):
                gloss = defn.get("gloss", "")

                cadre_def = ctk.CTkFrame(parent, fg_color="transparent")
                cadre_def.grid(row=row, column=0, sticky="ew",
                                padx=24, pady=(2, 2))
                cadre_def.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    cadre_def,
                    text=f"{i}.",
                    font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
                    text_color="#80C8A0",
                    width=24, anchor="ne",
                ).grid(row=0, column=0, sticky="ne", padx=(0, 6))

                ctk.CTkLabel(
                    cadre_def,
                    text=gloss,
                    font=ctk.CTkFont(family="Georgia", size=13),
                    text_color="#C8EED8",
                    wraplength=440,
                    anchor="nw", justify="left",
                ).grid(row=0, column=1, sticky="nw")
                row += 1

        ctk.CTkButton(
            parent,
            text="Voir le mot",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color="#2A5A3A",
            hover_color="#3A6A4A",
            text_color="#80C8A0",
            height=40, width=180, corner_radius=0,
            command=self._retourner_carte,
        ).grid(row=row, column=0, pady=(12, 24))

    # ------------------------------------------------------------------
    # Logique de session
    # ------------------------------------------------------------------

    def _demarrer_session(self):
        """Initialise une nouvelle session quiz."""
        if self.lexique.est_vide():
            self._afficher_ecran_attente()
            return

        mots = self.lexique.mots()
        random.shuffle(mots)
        self._mots_session = mots
        self._mots_vus = []
        self._mot_suivant()

    def _mot_suivant(self):
        """Passe au mot suivant dans la session."""
        if not self._mots_session:
            self._afficher_fin_session()
            return

        self._mot_courant = self._mots_session.pop(0)
        self._mots_vus.append(self._mot_courant)
        self._face_mot = True
        self._mettre_a_jour_progression()
        self._afficher_carte()

    def _retourner_carte(self):
        """Bascule entre face mot et face définition."""
        self._face_mot = not self._face_mot
        self._afficher_carte()

    def _mettre_a_jour_progression(self):
        total = len(self._mots_vus) + len(self._mots_session)
        vu = len(self._mots_vus)
        self._label_progression.configure(
            text=f"{vu} / {total}"
        )

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def rafraichir(self):
        """Appelé si le lexique a changé — réinitialise l'écran."""
        if self.lexique.est_vide():
            self._afficher_ecran_attente()
        elif not self._mot_courant:
            self._afficher_ecran_attente()