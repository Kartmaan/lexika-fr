"""
ui/tab_dictionnaire.py
----------------------
Onglet Dictionnaire : recherche, affichage des définitions, ajout au lexique.
"""

import customtkinter as ctk
from tkinter import StringVar


# Couleurs et styles centralisés
COULEUR_ACCENT    = "#4A9EFF"
COULEUR_SUCCES    = "#3DBE7A"
COULEUR_ERREUR    = "#FF5F5F"
COULEUR_NEUTRE    = "#8A8A9A"
COULEUR_SURFACE   = "#1E1E2E"
COULEUR_SURFACE2  = "#2A2A3E"
COULEUR_TEXTE     = "#E8E8F0"
COULEUR_TEXTE2    = "#A0A0B8"

POS_LABELS = {
    "N":   "Nom",
    "V":   "Verbe",
    "ADJ": "Adjectif",
    "ADV": "Adverbe",
    "PRO": "Pronom",
    "DET": "Déterminant",
    "PRE": "Préposition",
    "CON": "Conjonction",
    "INT": "Interjection",
    "?":   "Indéfini",
}


class TabDictionnaire(ctk.CTkFrame):
    """Onglet principal : recherche dans le dictionnaire."""

    def __init__(self, parent, dictionnaire, lexique, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.dictionnaire = dictionnaire
        self.lexique = lexique
        self._mot_courant: str | None = None
        self._lexemes_courants: list | None = None

        self._construire_ui()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _construire_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Barre de recherche ---
        barre = ctk.CTkFrame(self, fg_color=COULEUR_SURFACE, corner_radius=12,
                             border_width=1, border_color="#2E2E42")
        barre.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        barre.grid_columnconfigure(0, weight=1)

        self._var_recherche = StringVar()
        self._champ = ctk.CTkEntry(
            barre,
            textvariable=self._var_recherche,
            placeholder_text="Rechercher un mot…",
            font=ctk.CTkFont(family="Georgia", size=15),
            fg_color=COULEUR_SURFACE2,
            border_color="#3A3A5C",
            text_color=COULEUR_TEXTE,
            height=44,
            corner_radius=8,
        )
        self._champ.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="ew")
        self._champ.bind("<Return>", lambda e: self._lancer_recherche())

        self._btn_recherche = ctk.CTkButton(
            barre,
            text="Rechercher",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color=COULEUR_ACCENT,
            hover_color="#3A8EEF",
            text_color="white",
            height=44,
            width=130,
            corner_radius=8,
            command=self._lancer_recherche,
        )
        self._btn_recherche.grid(row=0, column=1, padx=(0, 16), pady=12)

        # --- Zone de résultat ---
        zone = ctk.CTkFrame(self, fg_color=COULEUR_SURFACE, corner_radius=12,
                            border_width=1, border_color="#2E2E42")
        zone.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        zone.grid_columnconfigure(0, weight=1)
        zone.grid_rowconfigure(1, weight=1)

        # Titre du mot défini
        self._titre = ctk.CTkLabel(
            zone,
            text="",
            font=ctk.CTkFont(family="Georgia", size=26, weight="bold"),
            text_color=COULEUR_TEXTE,
            anchor="w",
        )
        self._titre.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))

        # Zone scrollable pour les définitions
        self._zone_def = ctk.CTkScrollableFrame(
            zone,
            fg_color=COULEUR_SURFACE,
            scrollbar_button_color="#3A3A5C",
            scrollbar_button_hover_color=COULEUR_ACCENT,
            corner_radius=0,
        )
        self._zone_def.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._zone_def.grid_columnconfigure(0, weight=1)

        # Message d'accueil initial
        self._afficher_accueil()

        # --- Pied de page : bouton + message statut ---
        pied = ctk.CTkFrame(zone, fg_color="transparent")
        pied.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 16))
        pied.grid_columnconfigure(0, weight=1)

        self._label_statut = ctk.CTkLabel(
            pied,
            text="",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_NEUTRE,
            anchor="w",
        )
        self._label_statut.grid(row=0, column=0, sticky="w")

        self._btn_ajouter = ctk.CTkButton(
            pied,
            text="＋  Ajouter au lexique",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            fg_color=COULEUR_SUCCES,
            hover_color="#2EAA6A",
            text_color="white",
            height=38,
            width=180,
            corner_radius=8,
            state="disabled",
            command=self._ajouter_au_lexique,
        )
        self._btn_ajouter.grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------
    # Logique de recherche
    # ------------------------------------------------------------------

    def _lancer_recherche(self):
        mot = self._var_recherche.get().strip()
        if not mot:
            return

        self._vider_definitions()
        self._label_statut.configure(text="")

        lexemes = self.dictionnaire.rechercher(mot)

        if lexemes:
            self._mot_courant = mot.lower()
            self._lexemes_courants = lexemes
            self._afficher_definitions(mot, lexemes)
            self._btn_ajouter.configure(state="normal")
        else:
            self._mot_courant = None
            self._lexemes_courants = None
            self._btn_ajouter.configure(state="disabled")
            self._afficher_introuvable(mot)

    def _ajouter_au_lexique(self):
        if not self._mot_courant or not self._lexemes_courants:
            return

        if self.lexique.contient(self._mot_courant):
            self._label_statut.configure(
                text=f"« {self._mot_courant} » est déjà dans votre lexique.",
                text_color=COULEUR_NEUTRE,
            )
            return

        ok = self.lexique.ajouter_depuis_dictionnaire(
            self._mot_courant, self._lexemes_courants
        )
        if ok:
            self._label_statut.configure(
                text=f"✓  « {self._mot_courant} » ajouté au lexique.",
                text_color=COULEUR_SUCCES,
            )
            self._btn_ajouter.configure(state="disabled")
        else:
            self._label_statut.configure(
                text="Erreur lors de l'ajout.",
                text_color=COULEUR_ERREUR,
            )

    # ------------------------------------------------------------------
    # Affichage des définitions
    # ------------------------------------------------------------------

    def _vider_definitions(self):
        for widget in self._zone_def.winfo_children():
            widget.destroy()
        self._titre.configure(text="")

    def _afficher_accueil(self):
        label = ctk.CTkLabel(
            self._zone_def,
            text="Saisissez un mot dans le champ de recherche ci-dessus.",
            font=ctk.CTkFont(family="Georgia", size=14),
            text_color=COULEUR_NEUTRE,
            wraplength=600,
            anchor="w",
            justify="left",
        )
        label.grid(row=0, column=0, sticky="w", padx=16, pady=20)

    def _afficher_introuvable(self, mot: str):
        self._titre.configure(text=f"« {mot} » introuvable")

        suggestions = self.dictionnaire.suggerer(mot)

        if not suggestions:
            label = ctk.CTkLabel(
                self._zone_def,
                text="Aucun mot proche trouvé. Vérifiez l'orthographe.",
                font=ctk.CTkFont(family="Georgia", size=14),
                text_color=COULEUR_ERREUR,
                anchor="w",
            )
            label.grid(row=0, column=0, sticky="w", padx=16, pady=20)
            return

        intro = ctk.CTkLabel(
            self._zone_def,
            text="Peut-être cherchiez-vous…",
            font=ctk.CTkFont(family="Georgia", size=13),
            text_color=COULEUR_NEUTRE,
            anchor="w",
        )
        intro.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        for i, suggestion in enumerate(suggestions):
            btn = ctk.CTkButton(
                self._zone_def,
                text=suggestion,
                font=ctk.CTkFont(family="Georgia", size=14),
                fg_color=COULEUR_SURFACE2,
                hover_color="#3A3A5C",
                text_color=COULEUR_ACCENT,
                height=34,
                anchor="w",
                corner_radius=6,
                command=lambda m=suggestion: self._rechercher_suggestion(m),
            )
            btn.grid(row=i + 1, column=0, sticky="w", padx=16, pady=3)

    def _rechercher_suggestion(self, mot: str):
        self._var_recherche.set(mot)
        self._lancer_recherche()

    def _afficher_definitions(self, mot: str, lexemes: list):
        self._titre.configure(text=mot.capitalize())

        row = 0
        for lexeme in lexemes:
            pos = lexeme.get("pos", "?")
            pos_label = POS_LABELS.get(pos, pos)

            # Badge POS
            badge = ctk.CTkLabel(
                self._zone_def,
                text=f"  {pos_label}  ",
                font=ctk.CTkFont(family="Georgia", size=11, weight="bold"),
                fg_color="#3A3A5C",
                text_color=COULEUR_ACCENT,
                corner_radius=4,
                height=22,
            )
            badge.grid(row=row, column=0, sticky="w", padx=16, pady=(16, 4))
            row += 1

            for i, defn in enumerate(lexeme.get("definitions", []), 1):
                row = self._afficher_une_def(row, i, defn, niveau=0)

        # Séparateur de fin
        sep = ctk.CTkFrame(self._zone_def, height=1, fg_color="#3A3A5C")
        sep.grid(row=row, column=0, sticky="ew", padx=16, pady=(12, 8))

    def _afficher_une_def(self, row: int, numero, defn: dict, niveau: int) -> int:
        """Affiche une définition (toplevel ou sublevel) et retourne la prochaine row."""
        pad_gauche = 16 + niveau * 24

        # Ligne numéro + gloss
        gloss = defn.get("gloss", "")
        register = defn.get("register")
        semantic = defn.get("semantic")
        domain = defn.get("domain")

        # Préfixe de numérotation
        if niveau == 0:
            prefixe = f"{numero}."
        else:
            prefixe = f"  {numero}."

        # Étiquettes contextuelles (register, semantic, domain)
        tags = []
        if register:
            tags.append(f"({register})")
        if semantic:
            tags.append(f"[{semantic}]")
        if domain:
            tags.append(f"‹{domain}›")
        tag_str = "  ".join(tags)

        if tag_str:
            tag_label = ctk.CTkLabel(
                self._zone_def,
                text=tag_str,
                font=ctk.CTkFont(family="Georgia", size=11, slant="italic"),
                text_color="#7A8AB8",
                anchor="w",
            )
            tag_label.grid(row=row, column=0, sticky="w",
                           padx=pad_gauche + 20, pady=(4, 0))
            row += 1

        frame_def = ctk.CTkFrame(
            self._zone_def, fg_color="transparent"
        )
        frame_def.grid(row=row, column=0, sticky="ew",
                       padx=pad_gauche, pady=(2, 2))
        frame_def.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame_def,
            text=prefixe,
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=COULEUR_ACCENT,
            width=30,
            anchor="ne",
        ).grid(row=0, column=0, sticky="ne", padx=(0, 6), pady=0)

        ctk.CTkLabel(
            frame_def,
            text=gloss,
            font=ctk.CTkFont(family="Georgia", size=14),
            text_color=COULEUR_TEXTE,
            wraplength=560,
            anchor="nw",
            justify="left",
        ).grid(row=0, column=1, sticky="nw", pady=0)
        row += 1

        # Exemples
        for ex in defn.get("exemples", []):
            ex_label = ctk.CTkLabel(
                self._zone_def,
                text=f"  « {ex} »",
                font=ctk.CTkFont(family="Georgia", size=12, slant="italic"),
                text_color=COULEUR_TEXTE2,
                wraplength=540,
                anchor="w",
                justify="left",
            )
            ex_label.grid(row=row, column=0, sticky="w",
                          padx=pad_gauche + 20, pady=(1, 1))
            row += 1

        # Sous-définitions
        for j, sous_def in enumerate(defn.get("sous_definitions", []), 1):
            row = self._afficher_une_def(row, f"{numero}.{j}", sous_def, niveau=1)

        return row

    # ------------------------------------------------------------------
    # API publique — appelée depuis l'onglet Lexique
    # ------------------------------------------------------------------

    def afficher_depuis_lexique(self, mot: str, entree: dict):
        """Affiche le mot et ses définitions depuis le lexique (sans recherche SQL)."""
        self._vider_definitions()
        self._label_statut.configure(text="")
        self._var_recherche.set(mot)
        self._mot_courant = mot
        self._lexemes_courants = entree.get("lexemes", [])
        self._afficher_definitions(mot, self._lexemes_courants)

        # Bouton d'ajout inutile — déjà dans le lexique
        self._btn_ajouter.configure(state="disabled")
        self._label_statut.configure(
            text=f"« {mot} » est déjà dans votre lexique.",
            text_color=COULEUR_NEUTRE,
        )
