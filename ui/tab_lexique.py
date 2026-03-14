"""
ui/tab_lexique.py
-----------------
Onglet Lexique : affichage deux colonnes, ajout personnalisé, suppression,
import/export JSON.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

COULEUR_ACCENT   = "#4A9EFF"
COULEUR_SUCCES   = "#3DBE7A"
COULEUR_ERREUR   = "#FF5F5F"
COULEUR_NEUTRE   = "#8A8A9A"
COULEUR_SURFACE  = "#1E1E2E"
COULEUR_SURFACE2 = "#2A2A3E"
COULEUR_SURFACE3 = "#14141F"
COULEUR_TEXTE    = "#E8E8F0"
COULEUR_TEXTE2   = "#A0A0B8"

POS_LABELS = {
    "N": "Nom", "V": "Verbe", "ADJ": "Adjectif", "ADV": "Adverbe",
    "PRO": "Pronom", "DET": "Déterminant", "PRE": "Préposition",
    "CON": "Conjonction", "INT": "Interjection", "?": "Indéfini",
}


class TabLexique(ctk.CTkFrame):
    """Onglet de gestion du lexique personnel."""

    def __init__(self, parent, lexique, on_voir_dans_dico=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.lexique = lexique
        self.on_voir_dans_dico = on_voir_dans_dico  # callback vers l'onglet dico
        self._mot_selectionne: str | None = None
        self._boutons_vignettes: dict[str, ctk.CTkButton] = {}

        self._construire_ui()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _construire_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- En-tête avec actions ---
        entete = ctk.CTkFrame(self, fg_color=COULEUR_SURFACE, corner_radius=12,
                              border_width=1, border_color="#2E2E42")
        entete.grid(row=0, column=0, columnspan=2, sticky="ew",
                    padx=20, pady=(20, 10))

        ctk.CTkLabel(
            entete,
            text="Mon Lexique",
            font=ctk.CTkFont(family="Georgia", size=18, weight="bold"),
            text_color=COULEUR_TEXTE,
        ).pack(side="left", padx=16, pady=12)

        self._label_compteur = ctk.CTkLabel(
            entete,
            text=self._texte_compteur(),
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_NEUTRE,
        )
        self._label_compteur.pack(side="left", padx=(0, 16), pady=12)

        # Boutons d'action
        for texte, couleur, hover, cmd in [
            ("＋ Mot personnalisé", "#5A4E8A", "#6A5E9A", self._ouvrir_formulaire_perso),
            ("⬆ Exporter",         COULEUR_SURFACE2, "#3A3A5C", self._exporter),
            ("⬇ Importer",         COULEUR_SURFACE2, "#3A3A5C", self._importer),
        ]:
            ctk.CTkButton(
                entete, text=texte,
                font=ctk.CTkFont(family="Georgia", size=13),
                fg_color=couleur, hover_color=hover,
                text_color=COULEUR_TEXTE,
                height=34, corner_radius=8,
                command=cmd,
            ).pack(side="right", padx=6, pady=10)

        # --- Colonne gauche : liste des mots ---
        colonne_gauche = ctk.CTkFrame(
            self, fg_color=COULEUR_SURFACE3, corner_radius=12, width=220,
            border_width=1, border_color="#2E2E42"
        )
        colonne_gauche.grid(row=1, column=0, sticky="nsew",
                            padx=(20, 6), pady=(0, 20))
        colonne_gauche.grid_propagate(False)
        colonne_gauche.grid_rowconfigure(0, weight=1)
        colonne_gauche.grid_columnconfigure(0, weight=1)

        self._liste_mots = ctk.CTkScrollableFrame(
            colonne_gauche,
            fg_color="transparent",
            scrollbar_button_color="#3A3A5C",
            scrollbar_button_hover_color=COULEUR_ACCENT,
        )
        self._liste_mots.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._liste_mots.grid_columnconfigure(0, weight=1)

        # --- Colonne droite : définitions ---
        self._colonne_droite = ctk.CTkFrame(
            self, fg_color=COULEUR_SURFACE, corner_radius=12,
            border_width=1, border_color="#2E2E42"
        )
        self._colonne_droite.grid(row=1, column=1, sticky="nsew",
                                  padx=(6, 20), pady=(0, 20))
        self._colonne_droite.grid_columnconfigure(0, weight=1)
        self._colonne_droite.grid_rowconfigure(1, weight=1)

        self._titre_def = ctk.CTkLabel(
            self._colonne_droite,
            text="",
            font=ctk.CTkFont(family="Georgia", size=22, weight="bold"),
            text_color=COULEUR_TEXTE,
            anchor="w",
        )
        self._titre_def.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))

        self._zone_def = ctk.CTkScrollableFrame(
            self._colonne_droite,
            fg_color="transparent",
            scrollbar_button_color="#3A3A5C",
            scrollbar_button_hover_color=COULEUR_ACCENT,
        )
        self._zone_def.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._zone_def.grid_columnconfigure(0, weight=1)

        # Actions sur le mot sélectionné
        pied = ctk.CTkFrame(self._colonne_droite, fg_color="transparent")
        pied.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 16))
        pied.grid_columnconfigure(0, weight=1)

        self._btn_voir_dico = ctk.CTkButton(
            pied,
            text="Voir dans le dictionnaire",
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color=COULEUR_SURFACE2,
            hover_color="#3A3A5C",
            text_color=COULEUR_ACCENT,
            height=34, corner_radius=8,
            state="disabled",
            command=self._voir_dans_dico,
        )
        self._btn_voir_dico.grid(row=0, column=0, sticky="w")

        self._btn_supprimer = ctk.CTkButton(
            pied,
            text="🗑  Supprimer du lexique",
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color="#4A1A1A",
            hover_color="#6A2A2A",
            text_color=COULEUR_ERREUR,
            height=34, corner_radius=8,
            state="disabled",
            command=self._supprimer_mot,
        )
        self._btn_supprimer.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Remplir la liste
        self._rafraichir_liste()
        self._afficher_placeholder()

    # ------------------------------------------------------------------
    # Liste des mots (colonne gauche)
    # ------------------------------------------------------------------

    def _rafraichir_liste(self):
        for w in self._liste_mots.winfo_children():
            w.destroy()
        self._boutons_vignettes.clear()

        mots = self.lexique.mots()

        if not mots:
            ctk.CTkLabel(
                self._liste_mots,
                text="Lexique vide.\nAjoutez des mots\ndepuis le Dictionnaire.",
                font=ctk.CTkFont(family="Georgia", size=12),
                text_color=COULEUR_NEUTRE,
                justify="center",
            ).grid(row=0, column=0, pady=20, padx=8)
            return

        for i, mot in enumerate(mots):
            entree = self.lexique.obtenir(mot)
            est_perso = entree and entree.get("source") == "personnalisé"

            couleur_fg = "#2A2A4A" if not est_perso else "#2A1A3A"
            couleur_texte = COULEUR_TEXTE if not est_perso else "#C8A8FF"

            btn = ctk.CTkButton(
                self._liste_mots,
                text=mot.capitalize(),
                font=ctk.CTkFont(family="Georgia", size=13),
                fg_color=couleur_fg,
                hover_color="#3A3A5C",
                text_color=couleur_texte,
                height=36,
                anchor="w",
                corner_radius=6,
                command=lambda m=mot: self._selectionner_mot(m),
            )
            btn.grid(row=i, column=0, sticky="ew", padx=8, pady=3)
            self._boutons_vignettes[mot] = btn

        self._label_compteur.configure(text=self._texte_compteur())

    def _selectionner_mot(self, mot: str):
        # Réinitialiser l'ancienne sélection
        if self._mot_selectionne and self._mot_selectionne in self._boutons_vignettes:
            entree_prec = self.lexique.obtenir(self._mot_selectionne)
            est_perso = entree_prec and entree_prec.get("source") == "personnalisé"
            self._boutons_vignettes[self._mot_selectionne].configure(
                fg_color="#2A1A3A" if est_perso else "#2A2A4A"
            )

        self._mot_selectionne = mot
        if mot in self._boutons_vignettes:
            self._boutons_vignettes[mot].configure(fg_color="#3A4A7A")

        entree = self.lexique.obtenir(mot)
        if entree:
            self._afficher_definition(mot, entree)
            self._btn_supprimer.configure(state="normal")
            # Bouton "voir dans dico" seulement si source = dictionnaire
            if entree.get("source") == "dictionnaire" and self.on_voir_dans_dico:
                self._btn_voir_dico.configure(state="normal")
            else:
                self._btn_voir_dico.configure(state="disabled")

    # ------------------------------------------------------------------
    # Affichage définition (colonne droite)
    # ------------------------------------------------------------------

    def _afficher_placeholder(self):
        for w in self._zone_def.winfo_children():
            w.destroy()
        self._titre_def.configure(text="")
        ctk.CTkLabel(
            self._zone_def,
            text="Sélectionnez un mot dans la liste.",
            font=ctk.CTkFont(family="Georgia", size=13),
            text_color=COULEUR_NEUTRE,
        ).grid(row=0, column=0, pady=20, padx=16)

    def _afficher_definition(self, mot: str, entree: dict):
        for w in self._zone_def.winfo_children():
            w.destroy()

        self._titre_def.configure(text=mot.capitalize())

        source = entree.get("source", "dictionnaire")
        if source == "personnalisé":
            ctk.CTkLabel(
                self._zone_def,
                text="  ✎ Mot personnalisé",
                font=ctk.CTkFont(family="Georgia", size=11, slant="italic"),
                text_color="#9A78C8",
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=16, pady=(8, 4))

        row = 1
        for lexeme in entree.get("lexemes", []):
            pos = lexeme.get("pos", "?")
            pos_label = POS_LABELS.get(pos, pos)

            badge = ctk.CTkLabel(
                self._zone_def,
                text=f"  {pos_label}  ",
                font=ctk.CTkFont(family="Georgia", size=11, weight="bold"),
                fg_color="#3A3A5C",
                text_color=COULEUR_ACCENT,
                corner_radius=4,
                height=22,
            )
            badge.grid(row=row, column=0, sticky="w", padx=16, pady=(10, 4))
            row += 1

            for i, defn in enumerate(lexeme.get("definitions", []), 1):
                row = self._afficher_une_def(row, i, defn)

    def _afficher_une_def(self, row: int, numero, defn: dict) -> int:
        gloss = defn.get("gloss", "")
        tags = " ".join(filter(None, [
            f"({defn['register']})" if defn.get("register") else "",
            f"[{defn['semantic']}]" if defn.get("semantic") else "",
        ]))

        if tags:
            ctk.CTkLabel(
                self._zone_def,
                text=tags,
                font=ctk.CTkFont(family="Georgia", size=11, slant="italic"),
                text_color="#7A8AB8",
                anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=36, pady=(4, 0))
            row += 1

        frame = ctk.CTkFrame(self._zone_def, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(2, 2))
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text=f"{numero}.",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=COULEUR_ACCENT,
            width=28, anchor="ne",
        ).grid(row=0, column=0, sticky="ne", padx=(0, 6))

        ctk.CTkLabel(
            frame,
            text=gloss,
            font=ctk.CTkFont(family="Georgia", size=14),
            text_color=COULEUR_TEXTE,
            wraplength=420,
            anchor="nw", justify="left",
        ).grid(row=0, column=1, sticky="nw")
        row += 1

        for ex in defn.get("exemples", []):
            ctk.CTkLabel(
                self._zone_def,
                text=f"  « {ex} »",
                font=ctk.CTkFont(family="Georgia", size=12, slant="italic"),
                text_color=COULEUR_TEXTE2,
                wraplength=420,
                anchor="w", justify="left",
            ).grid(row=row, column=0, sticky="w", padx=36, pady=(1, 1))
            row += 1

        for j, sous in enumerate(defn.get("sous_definitions", []), 1):
            row = self._afficher_une_def(row, f"{numero}.{j}", sous)

        return row

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _supprimer_mot(self):
        if not self._mot_selectionne:
            return
        ok = messagebox.askyesno(
            "Supprimer",
            f"Supprimer « {self._mot_selectionne} » du lexique ?",
        )
        if ok:
            self.lexique.supprimer(self._mot_selectionne)
            self._mot_selectionne = None
            self._btn_supprimer.configure(state="disabled")
            self._btn_voir_dico.configure(state="disabled")
            self._rafraichir_liste()
            self._afficher_placeholder()

    def _voir_dans_dico(self):
        if self._mot_selectionne and self.on_voir_dans_dico:
            entree = self.lexique.obtenir(self._mot_selectionne)
            if entree:
                self.on_voir_dans_dico(self._mot_selectionne, entree)

    def _exporter(self):
        chemin = filedialog.asksaveasfilename(
            title="Exporter le lexique",
            defaultextension=".json",
            filetypes=[("Fichier JSON", "*.json")],
            initialfile="mon_lexique.json",
        )
        if chemin:
            ok = self.lexique.exporter(chemin)
            if ok:
                messagebox.showinfo("Export réussi",
                                    f"Lexique exporté avec succès :\n{chemin}")
            else:
                messagebox.showerror("Erreur", "L'export a échoué.")

    def _importer(self):
        chemin = filedialog.askopenfilename(
            title="Importer un lexique",
            filetypes=[("Fichier JSON", "*.json")],
        )
        if chemin:
            ok, msg = self.lexique.importer(chemin)
            if ok:
                messagebox.showinfo("Import réussi", msg)
                self._rafraichir_liste()
            else:
                messagebox.showerror("Erreur d'import", msg)

    def _ouvrir_formulaire_perso(self):
        FormulaireMotPerso(self, self.lexique, self._on_mot_perso_ajoute)

    def _on_mot_perso_ajoute(self):
        self._rafraichir_liste()

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def rafraichir(self):
        """Appelé depuis d'autres onglets après modification du lexique."""
        self._rafraichir_liste()

    def _texte_compteur(self) -> str:
        n = self.lexique.nombre_mots()
        return f"({n} mot{'s' if n > 1 else ''})"


# ---------------------------------------------------------------------------
# Formulaire d'ajout de mot personnalisé
# ---------------------------------------------------------------------------

class FormulaireMotPerso(ctk.CTkToplevel):
    """Fenêtre modale pour ajouter un mot personnalisé au lexique."""

    def __init__(self, parent, lexique, callback_succes):
        super().__init__(parent)
        self.lexique = lexique
        self.callback_succes = callback_succes

        self.title("Ajouter un mot personnalisé")
        self.geometry("520x520")
        self.resizable(False, False)
        self.configure(fg_color=COULEUR_SURFACE)

        self._champs_definitions: list[ctk.CTkTextbox] = []

        # Différer la construction et le grab pour éviter la fenêtre vide sur Linux
        self.after(50, self._post_init)

    def _post_init(self):
        self._construire()
        self.lift()
        self.focus_set()
        self.grab_set()

    def _construire(self):
        self.grid_columnconfigure(0, weight=1)
        self.update_idletasks()   # force le rendu de la fenêtre avant d'ajouter les widgets

        ctk.CTkLabel(
            self,
            text="Nouveau mot personnalisé",
            font=ctk.CTkFont(family="Georgia", size=18, weight="bold"),
            text_color=COULEUR_TEXTE,
        ).grid(row=0, column=0, pady=(20, 4), padx=24, sticky="w")

        ctk.CTkLabel(
            self,
            text="Ce mot sera ajouté à votre lexique avec vos propres définitions.",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_NEUTRE,
        ).grid(row=1, column=0, padx=24, sticky="w", pady=(0, 12))

        # Champ mot
        ctk.CTkLabel(
            self,
            text="Mot",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color=COULEUR_TEXTE2,
        ).grid(row=2, column=0, padx=24, sticky="w")

        self._champ_mot = ctk.CTkEntry(
            self,
            font=ctk.CTkFont(family="Georgia", size=14),
            fg_color=COULEUR_SURFACE2,
            border_color="#3A3A5C",
            text_color=COULEUR_TEXTE,
            height=40,
            corner_radius=8,
        )
        self._champ_mot.grid(row=3, column=0, padx=24, pady=(4, 12), sticky="ew")

        # Définitions
        ctk.CTkLabel(
            self,
            text="Définition(s)",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color=COULEUR_TEXTE2,
        ).grid(row=4, column=0, padx=24, sticky="w")

        self._frame_defs = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=160,
        )
        self._frame_defs.grid(row=5, column=0, padx=24, pady=(4, 8), sticky="ew")
        self._frame_defs.grid_columnconfigure(0, weight=1)

        self._ajouter_champ_definition()

        ctk.CTkButton(
            self,
            text="＋  Ajouter une définition",
            font=ctk.CTkFont(family="Georgia", size=12),
            fg_color=COULEUR_SURFACE2,
            hover_color="#3A3A5C",
            text_color=COULEUR_ACCENT,
            height=30, corner_radius=6,
            command=self._ajouter_champ_definition,
        ).grid(row=6, column=0, padx=24, pady=(0, 12), sticky="w")

        self._label_erreur = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COULEUR_ERREUR,
        )
        self._label_erreur.grid(row=7, column=0, padx=24, sticky="w")

        # Boutons Valider / Annuler
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=8, column=0, padx=24, pady=(8, 20), sticky="e")

        ctk.CTkButton(
            btns, text="Annuler",
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color=COULEUR_SURFACE2,
            hover_color="#3A3A5C",
            text_color=COULEUR_TEXTE,
            height=38, width=100, corner_radius=8,
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns, text="Ajouter",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            fg_color=COULEUR_SUCCES,
            hover_color="#2EAA6A",
            text_color="white",
            height=38, width=100, corner_radius=8,
            command=self._valider,
        ).pack(side="left")

    def _ajouter_champ_definition(self):
        i = len(self._champs_definitions)
        tb = ctk.CTkTextbox(
            self._frame_defs,
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color=COULEUR_SURFACE2,
            border_color="#3A3A5C",
            text_color=COULEUR_TEXTE,
            height=60,
            corner_radius=8,
            border_width=1,
            wrap="word",
        )
        tb.grid(row=i, column=0, pady=(0, 6), sticky="ew")
        self._champs_definitions.append(tb)

    def _valider(self):
        mot = self._champ_mot.get().strip()
        if not mot:
            self._label_erreur.configure(text="Le champ « Mot » est obligatoire.")
            return

        definitions = [
            tb.get("1.0", "end").strip()
            for tb in self._champs_definitions
            if tb.get("1.0", "end").strip()
        ]
        if not definitions:
            self._label_erreur.configure(
                text="Saisissez au moins une définition."
            )
            return

        ok = self.lexique.ajouter_personnalise(mot, definitions)
        if not ok:
            self._label_erreur.configure(
                text=f"« {mot} » est déjà présent dans le lexique."
            )
            return

        self.callback_succes()
        self.destroy()
