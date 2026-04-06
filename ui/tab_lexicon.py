"""
ui/tab_lexicon.py
-----------------
Lexicon tab: two-column layout, custom word form, delete, import/export.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.config import FONTS, COLORS, POS_LABELS, GENDER_LABELS, GENDER_COLORS

def _bind_mousewheel(scrollable_frame):
    """Enables mouse wheel scrolling on a CTkScrollableFrame (Linux + Windows)."""
    canvas = scrollable_frame._parent_canvas

    def scroll(delta):
        canvas.yview_scroll(delta, "units")

    def on_enter(_):
        scrollable_frame.bind_all("<Button-4>",   lambda e: scroll(-1))
        scrollable_frame.bind_all("<Button-5>",   lambda e: scroll(1))
        scrollable_frame.bind_all("<MouseWheel>", lambda e: scroll(int(-1 * e.delta / 120)))

    def on_leave(_):
        scrollable_frame.unbind_all("<Button-4>")
        scrollable_frame.unbind_all("<Button-5>")
        scrollable_frame.unbind_all("<MouseWheel>")

    scrollable_frame.bind("<Enter>", on_enter, add="+")
    scrollable_frame.bind("<Leave>", on_leave, add="+")

class TabLexicon(ctk.CTkFrame):
    """Personal lexicon management tab."""

    def __init__(self, parent, lexicon, view_in_dict=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.lexicon = lexicon
        self.on_view_in_dict = view_in_dict
        self._selected_word: str | None = None
        self._word_buttons: dict[str, ctk.CTkButton] = {}
        self._search_var = ctk.StringVar()

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Header with action buttons ---
        header = ctk.CTkFrame(self, fg_color=COLORS["SURFACE"], corner_radius=0,
                              border_width=1, border_color="#2E2E42")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="My Lexicon",
            font=ctk.CTkFont(family=FONTS["LEX_TITLE"][0], size=FONTS["LEX_TITLE"][1], weight=FONTS["LEX_TITLE"][2]),
            text_color=COLORS["TEXT"],
        ).pack(side="left", padx=16, pady=12)

        self._count_label = ctk.CTkLabel(
            header,
            text=self._count_text(),
            font=ctk.CTkFont(family=FONTS["LEX_COUNT"][0], size=FONTS["LEX_COUNT"][1]),
            text_color=COLORS["NEUTRAL"],
        )
        self._count_label.pack(side="left", padx=(0, 16), pady=12)

        for text, color, hover, cmd in [
            ("+ Custom word", COLORS["LEX_CUST_BTN"], COLORS["LEX_CUST_BTN_HOVER"], self._open_custom_form),
            ("Export",        COLORS["SURFACE2"], COLORS["ACCENT"], self._export),
            ("Import",        COLORS["SURFACE2"], COLORS["ACCENT"], self._import),
        ]:
            ctk.CTkButton(
                header, text=text,
                font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1]),
                fg_color=color, hover_color=hover,
                text_color=COLORS["TEXT"],
                height=34, corner_radius=0,
                command=cmd,
            ).pack(side="right", padx=6, pady=10)

        # --- Left column: word list ---
        left_col = ctk.CTkFrame(
            self, fg_color=COLORS["SURFACE3"], corner_radius=0, width=220,
            border_width=1, border_color="#2E2E42"
        )
        left_col.grid(row=1, column=0, sticky="nsew", padx=(20, 6), pady=(0, 20))
        left_col.grid_propagate(False)
        left_col.grid_rowconfigure(1, weight=1)   # row 0 = search bar, row 1 = list
        left_col.grid_columnconfigure(0, weight=1)

        # --- Search bar ---
        search_bar = ctk.CTkFrame(left_col, fg_color="transparent")
        search_bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        search_bar.grid_columnconfigure(0, weight=1)

        # Entry for live search filtering. The _refresh_list method will read 
        # the current value of self._search_var to filter the word list.
        self._search_entry = ctk.CTkEntry(
            search_bar,
            textvariable=self._search_var,
            placeholder_text="Search...",
            font=ctk.CTkFont(family=FONTS["LEX_LABEL"][0], size=FONTS["LEX_LABEL"][1]),
            fg_color=COLORS["SURFACE2"], border_color="#3A3A5C",
            text_color=COLORS["TEXT"], height=30, corner_radius=0,
        )
        self._search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        # Reset search button (X) to clear the search field and show the full list again
        ctk.CTkButton(
            search_bar,
            text="X",
            font=ctk.CTkFont(family=FONTS["LEX_LABEL"][0], size=11),
            fg_color=COLORS["SURFACE2"], hover_color=COLORS["LEX_RESET_BTN_HOVER"],
            text_color=COLORS["TEXT"],
            width=30, height=30, corner_radius=0,
            command=self._reset_search,
        ).grid(row=0, column=1)

        # Trigger live filtering on every keystroke
        self._search_var.trace_add("write", lambda *_: self._refresh_list())

        # --- Word list ---
        self._word_list = ctk.CTkScrollableFrame(
            left_col,
            fg_color="transparent",
            scrollbar_button_color=COLORS["SCROLLBAR"],
            scrollbar_button_hover_color=COLORS["ACCENT"],
        )
        self._word_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._word_list.grid_columnconfigure(0, weight=1)
        _bind_mousewheel(self._word_list)

        # --- Right column: definitions ---
        self._right_column = ctk.CTkFrame(
            self, fg_color=COLORS["SURFACE"], corner_radius=0,
            border_width=1, border_color="#2E2E42"
        )
        self._right_column.grid(row=1, column=1, sticky="nsew", padx=(6, 20), pady=(0, 20))
        self._right_column.grid_columnconfigure(0, weight=1)
        self._right_column.grid_rowconfigure(1, weight=1)

        self._def_title = ctk.CTkLabel(
            self._right_column,
            text="",
            font=ctk.CTkFont(family=FONTS["LEX_DEF_TITLE"][0], size=FONTS["LEX_DEF_TITLE"][1], weight=FONTS["LEX_DEF_TITLE"][2]),
            text_color=COLORS["TEXT"],
            anchor="w",
        )
        self._def_title.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))

        self._def_frame = ctk.CTkScrollableFrame(
            self._right_column,
            fg_color="transparent",
            scrollbar_button_color=COLORS["SCROLLBAR"],
            scrollbar_button_hover_color=COLORS["ACCENT"],
        )
        self._def_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._def_frame.grid_columnconfigure(0, weight=1)
        _bind_mousewheel(self._def_frame)

        # Action buttons (bottom of right column)
        action_bar = ctk.CTkFrame(self._right_column, fg_color="transparent")
        action_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 16))
        action_bar.grid_columnconfigure(0, weight=1)

        self._btn_view_dict = ctk.CTkButton(
            action_bar,
            text="View in dictionary",
            font=ctk.CTkFont(family=FONTS["LEX_LABEL"][0], size=FONTS["LEX_LABEL"][1]),
            fg_color=COLORS["SURFACE2"], hover_color="#3A3A5C",
            text_color=COLORS["ACCENT"],
            height=34, corner_radius=0, state="disabled",
            command=self._view_in_dict,
        )
        self._btn_view_dict.grid(row=0, column=0, sticky="w")

        # Delete button to remove the selected word from the lexicon. Only enabled when a word is selected.
        self._btn_delete = ctk.CTkButton(
            action_bar,
            text="Remove from lexicon",
            font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1]),
            fg_color=COLORS["TAB_BTN_DELETE"], hover_color=COLORS["TAB_BTN_DELETE_HOVER"],
            text_color=COLORS["ERROR"],
            height=34, corner_radius=0, state="disabled",
            command=self._delete_word,
        )
        self._btn_delete.grid(row=0, column=1, sticky="e", padx=(8, 0))

        self._refresh_list()
        self._show_placeholder()

    # ------------------------------------------------------------------
    # Word list (left column)
    # ------------------------------------------------------------------

    def _reset_search(self):
        """Clears the search field and restores the full word list."""
        self._search_var.set("")
        self._search_entry.focus_set()

    def _refresh_list(self):
        """Refreshes the word list, filtered by the current search query."""

        # Clear existing buttons
        for w in self._word_list.winfo_children():
            w.destroy()
        self._word_buttons.clear()

        query = self._search_var.get().strip().lower()
        all_words = self.lexicon.words()

        # Filter by query if one is active
        words = (
            [w for w in all_words if w.lower().startswith(query)]
            if query else all_words
        )

        # If the lexicon is empty, show a placeholder message instead of an empty list.
        if not all_words:
            ctk.CTkLabel(
                self._word_list,
                text="Lexicon is empty.\nAdd words from\nthe Dictionary tab.",
                font=ctk.CTkFont(family=FONTS["LEX_LABEL"][0], size=FONTS["LEX_LABEL"][1]),
                text_color=COLORS["NEUTRAL"],
                justify="center",
            ).grid(row=0, column=0, pady=20, padx=8)
            return

        # Create a button for each word in the lexicon. Custom words are visually distinguished.
        for i, word in enumerate(words):
            entry = self.lexicon.get(word)
            is_custom = entry and entry.get("source") == "custom"

            # Words vignetted with a different background color if they are custom entries, 
            # and a hover effect for better interactivity.
            btn = ctk.CTkButton(
                self._word_list,
                text=word.capitalize(),
                font=ctk.CTkFont(family=FONTS["LEX_WRD_LIST"][0], size=FONTS["LEX_WRD_LIST"][1]),
                fg_color=COLORS["LEX_WORD_FRAME_CUST"] if is_custom else COLORS["LEX_WORD_FRAME"],
                hover_color=COLORS["LEX_WORD_FRAME_CUST_HOVER"] if is_custom else COLORS["LEX_WORD_FRAME_HOVER"],
                text_color=COLORS["LEX_TXT_WORD_CUST"] if is_custom else COLORS["LEX_TXT_WORD"],
                height=36, anchor="w", corner_radius=0,
                command=lambda w=word: self._select_word(w),
            )
            btn.grid(row=i, column=0, sticky="ew", padx=8, pady=3)
            self._word_buttons[word] = btn

        self._count_label.configure(text=self._count_text())

    def _select_word(self, word: str):
        """Handles selection of a word from the list, updating the definition 
        display and action buttons.
        
        Args:
            word: The selected word.
        """
        # Reset previous selection
        if self._selected_word and self._selected_word in self._word_buttons:
            prev_entry = self.lexicon.get(self._selected_word)
            is_custom = prev_entry and prev_entry.get("source") == "custom"
            self._word_buttons[self._selected_word].configure(
                fg_color="#2A1A3A" if is_custom else "#2A2A4A"
            )

        self._selected_word = word
        if word in self._word_buttons:
            self._word_buttons[word].configure(fg_color="#3A4A7A")

        entry = self.lexicon.get(word)
        if entry:
            self._show_definition(word, entry)
            self._btn_delete.configure(state="normal")
            if entry.get("source") == "dictionary" and self.on_view_in_dict:
                self._btn_view_dict.configure(state="normal")
            else:
                self._btn_view_dict.configure(state="disabled")

    # ------------------------------------------------------------------
    # Definition display (right column)
    # ------------------------------------------------------------------

    def _show_placeholder(self):
        """Shows a placeholder message in the definition area when no word is selected."""
        for w in self._def_frame.winfo_children():
            w.destroy()

        self._def_title.configure(text="")

        ctk.CTkLabel(
            self._def_frame,
            text="Select a word from the list.",
            font=ctk.CTkFont(family=FONTS["LEX_LABEL"][0], size=FONTS["LEX_LABEL"][1]),
            text_color=COLORS["NEUTRAL"],
        ).grid(row=0, column=0, pady=20, padx=16)

    def _show_definition(self, word: str, entry: dict):
        """Displays the definitions of the selected word in the right column.
        
        Args:
            word: The selected word.
            entry: The word entry containing its definitions.
        """
        for w in self._def_frame.winfo_children():
            w.destroy()

        self._def_title.configure(text=word.capitalize())

        if entry.get("source") == "custom":
            ctk.CTkLabel(
                self._def_frame,
                text="  (custom word)",
                font=ctk.CTkFont(family=FONTS["LEX_LABEL"][0], size=FONTS["LEX_LABEL"][1]),
                text_color="#9A78C8", anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=16, pady=(8, 4))

        row = 1
        for lexeme in entry.get("lexemes", []):
            pos_label = POS_LABELS.get(lexeme.get("pos", "?"), "?")

            gender      = lexeme.get("gender")
            show_gender = (lexeme.get("pos") == "N" and gender in GENDER_LABELS)

            badge_row = ctk.CTkFrame(self._def_frame, fg_color="transparent")
            badge_row.grid(row=row, column=0, sticky="w", padx=16, pady=(10, 4))
            row += 1

            ctk.CTkLabel(
                badge_row,
                text=f"  {pos_label}  ",
                font=ctk.CTkFont(family=FONTS["BADGE"][0], size=FONTS["BADGE"][1], weight=FONTS["BADGE"][2]),
                fg_color=COLORS["BADGE"], text_color=COLORS["ACCENT"],
                corner_radius=0, height=22,
            ).pack(side="left", padx=(0, 4))

            if show_gender:
                ctk.CTkLabel(
                    badge_row,
                    text=f"  {GENDER_LABELS[gender]}  ",
                    font=ctk.CTkFont(family=FONTS["BADGE"][0], size=FONTS["BADGE"][1], weight=FONTS["BADGE"][2]),
                    fg_color=COLORS["BADGE"], text_color=GENDER_COLORS[gender],
                    corner_radius=0, height=22,
                ).pack(side="left")

            # Display definitions for this lexeme, including gloss, tags, examples, and sub-definitions.
            for i, defn in enumerate(lexeme.get("definitions", []), 1):
                row = self._show_definition_item(row, i, defn)

    def _show_definition_item(self, row: int, number, defn: dict) -> int:
        """Displays a single definition item, including gloss, tags, examples, and sub-definitions.
        Returns the next available row index after rendering this item.
        
        Args:
            row: The starting row index to render this definition item.
            number: The definition number (e.g., 1, 2, or "1.1" for sub-definitions).
            defn: The definition dictionary containing gloss, tags, examples, and sub-definitions.
        
        Returns:
            The next available row index after rendering this item.
        """
        gloss = defn.get("gloss", "")
        tags = " ".join(filter(None, [
            f"({defn['register']})" if defn.get("register") else "",
            f"[{defn['semantic']}]" if defn.get("semantic") else "",
        ]))

        # Main gloss line with number and definition text
        if tags:
            ctk.CTkLabel(
                self._def_frame, text=tags,
                font=ctk.CTkFont(family=FONTS["TAG"][0], size=FONTS["TAG"][1], slant=FONTS["TAG"][3]),
                text_color="#7A8AB8", anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=36, pady=(4, 0))
            row += 1

        frame = ctk.CTkFrame(self._def_frame, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(2, 2))
        frame.grid_columnconfigure(1, weight=1)

        # Number label (1., 2., etc.)
        ctk.CTkLabel(
            frame, text=f"{number}.",
            font=ctk.CTkFont(family=FONTS["PREFIX_DEF"][0], size=FONTS["PREFIX_DEF"][1], weight=FONTS["PREFIX_DEF"][2]),
            text_color=COLORS["ACCENT"], width=28, anchor="ne",
        ).grid(row=0, column=0, sticky="ne", padx=(0, 6))

        # Gloss may contain multiple lines, so use a label with wraplength instead of an entry
        ctk.CTkLabel(
            frame, text=gloss,
            font=ctk.CTkFont(family=FONTS["DEFINITION"][0], size=FONTS["DEFINITION"][1]),
            text_color=COLORS["TEXT"], wraplength=420, anchor="nw", justify="left",
        ).grid(row=0, column=1, sticky="nw")
        row += 1

        # Examples
        for ex in defn.get("exemples", []):
            ctk.CTkLabel(
                self._def_frame, text=f"  \"{ex}\"",
                font=ctk.CTkFont(family=FONTS["EXAMPLE"][0], size=FONTS["EXAMPLE"][1], slant=FONTS["EXAMPLE"][3]),
                text_color=COLORS["TEXT2"], wraplength=420, anchor="w", justify="left",
            ).grid(row=row, column=0, sticky="w", padx=36, pady=(1, 1))
            row += 1

        # Sub-definitions (nested)
        for j, sub in enumerate(defn.get("sous_definitions", []), 1):
            row = self._show_definition_item(row, f"{number}.{j}", sub)

        return row

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _delete_word(self):
        """Removes the selected word from the lexicon after user confirmation."""
        if not self._selected_word:
            return
        ok = messagebox.askyesno(
            "Remove word",
            f"Remove '{self._selected_word}' from the lexicon?",
        )
        if ok:
            self.lexicon.remove(self._selected_word)
            self._selected_word = None
            self._btn_delete.configure(state="disabled")
            self._btn_view_dict.configure(state="disabled")
            self._refresh_list()
            self._show_placeholder()

    def _view_in_dict(self):
        """If the selected word is from the dictionary, trigger the 
        callback to view it in the Dictionary tab."""
        if self._selected_word and self.on_view_in_dict:
            entry = self.lexicon.get(self._selected_word)
            if entry:
                self.on_view_in_dict(self._selected_word, entry)

    def _export(self):
        """Exports the current lexicon to a JSON file chosen by the user."""
        path = filedialog.asksaveasfilename(
            title="Export lexicon",
            defaultextension=".json",
            filetypes=[("JSON file", "*.json")],
            initialfile="my_lexicon.json",
        )
        if path:
            ok = self.lexicon.export(path)
            if ok:
                messagebox.showinfo("Export successful", f"Lexicon exported to:\n{path}")
            else:
                messagebox.showerror("Error", "Export failed.")

    def _import(self):
        """Imports a lexicon from a JSON file chosen by the user, with confirmation."""
        path = filedialog.askopenfilename(
            title="Import a lexicon",
            filetypes=[("JSON file", "*.json")],
        )
        if path:
            ok, msg = self.lexicon.import_from(path)
            if ok:
                messagebox.showinfo("Import successful", msg)
                self._refresh_list()
            else:
                messagebox.showerror("Import error", msg)

    def _open_custom_form(self):
        """Opens the form to add a custom word to the lexicon."""
        CustomWordForm(self, self.lexicon, self._on_custom_word_added)

    def _on_custom_word_added(self):
        """Callback after a custom word is added to refresh the 
        list and show the new word."""
        self._refresh_list()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self):
        """Called from other tabs after the lexicon is modified.
        Ensures the word list and count are up to date."""
        self._refresh_list()

    def _count_text(self) -> str:
        """Returns a string with the current number of words in the lexicon."""
        n = self.lexicon.word_count()
        return f"({n} word{'s' if n > 1 else ''})"


# ---------------------------------------------------------------------------
# Custom word form dialog
# ---------------------------------------------------------------------------

class CustomWordForm(ctk.CTkToplevel):
    """Modal dialog for adding a custom word to the lexicon."""

    def __init__(self, parent, lexicon, success_callback):
        super().__init__(parent)
        self.lexicon = lexicon
        self.success_callback = success_callback

        self.title("Add a custom word")
        self.geometry("520x640")
        self.resizable(False, True)
        self.configure(fg_color=COLORS["SURFACE"])

        self._definition_fields: list[ctk.CTkTextbox] = []
        self.after(50, self._post_init)

    def _post_init(self):
        """Called shortly after initialization to ensure the window is fully 
        created before building the UI."""
        self._build()
        self.lift()
        self.focus_set()
        self.grab_set()

    def _build(self):
        """Constructs the UI elements of the custom word form."""
        self.grid_columnconfigure(0, weight=1)
        self.update_idletasks()

        ctk.CTkLabel(
            self,
            text="New custom word",
            font=ctk.CTkFont(family=FONTS["LEX_CUST_TITLE"][0], size=FONTS["LEX_CUST_TITLE"][1], weight=FONTS["LEX_CUST_TITLE"][2]),
            text_color=COLORS["TEXT"],
        ).grid(row=0, column=0, pady=(20, 4), padx=24, sticky="w")

        ctk.CTkLabel(
            self,
            text="This word will be added to your lexicon with your own definitions.",
            font=ctk.CTkFont(family=FONTS["LEX_LABEL"][0], size=FONTS["LEX_LABEL"][1]),
            text_color=COLORS["NEUTRAL"],
        ).grid(row=1, column=0, padx=24, sticky="w", pady=(0, 12))

        # Word field
        ctk.CTkLabel(
            self, text="Word",
            font=ctk.CTkFont(family=FONTS["LEX_CUST_CAT"][0], size=FONTS["LEX_CUST_CAT"][1], weight=FONTS["LEX_CUST_CAT"][2]),
            text_color=COLORS["TEXT2"],
        ).grid(row=2, column=0, padx=24, sticky="w")

        self._word_entry = ctk.CTkEntry(
            self,
            font=ctk.CTkFont(family=FONTS["LEX_CUST_ENTRY"][0], size=FONTS["LEX_CUST_ENTRY"][1]),
            fg_color=COLORS["SURFACE2"], border_color="#3A3A5C",
            text_color=COLORS["TEXT"], height=40, corner_radius=0,
        )
        self._word_entry.grid(row=3, column=0, padx=24, pady=(4, 12), sticky="ew")

        # Definitions
        ctk.CTkLabel(
            self, text="Definition(s)",
            font=ctk.CTkFont(family=FONTS["LEX_CUST_CAT"][0], size=FONTS["LEX_CUST_CAT"][1], weight=FONTS["LEX_CUST_CAT"][2]),
            text_color=COLORS["TEXT2"],
        ).grid(row=4, column=0, padx=24, sticky="w")

        self._definitions_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=160,
        )
        self._definitions_frame.grid(row=5, column=0, padx=24, pady=(4, 8), sticky="ew")
        self._definitions_frame.grid_columnconfigure(0, weight=1)

        self._add_definition_field() # Start with one definition field by default

        # Button to add more definition fields if the user wants to enter multiple 
        # definitions for the same word.
        ctk.CTkButton(
            self, text="+ Add a definition",
            font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1]),
            fg_color=COLORS["SURFACE2"], hover_color="#3A3A5C",
            text_color=COLORS["ACCENT"], height=30, corner_radius=0,
            command=self._add_definition_field,
        ).grid(row=6, column=0, padx=24, pady=(0, 12), sticky="w")

        self._error_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family=FONTS["LEX_LABEL"][0], size=FONTS["LEX_LABEL"][1]),
            text_color=COLORS["ERROR"],
        )
        self._error_label.grid(row=7, column=0, padx=24, sticky="w")

        # Confirm / Cancel buttons
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=8, column=0, padx=24, pady=(8, 20), sticky="e")

        # Cancel button simply closes the form without saving anything.
        ctk.CTkButton(
            buttons_frame, text="Cancel",
            font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1]),
            fg_color=COLORS["SURFACE2"], hover_color=COLORS["LEX_RESET_BTN_HOVER"],
            text_color=COLORS["TEXT"], height=38, width=100, corner_radius=0,
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        # Add button validates the input and, if valid, adds the new custom word to the lexicon and closes the form.
        ctk.CTkButton(
            buttons_frame, text="Add",
            font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1], weight="bold"),
            fg_color=COLORS["SUCCESS"], hover_color=COLORS["LEX_CUST_ADD_BTN_HOVER"],
            text_color="white", height=38, width=100, corner_radius=0,
            command=self._validate,
        ).pack(side="left")

    def _add_definition_field(self):
        """Adds a new text box for entering a definition."""
        i = len(self._definition_fields)
        tb = ctk.CTkTextbox(
            self._definitions_frame,
            font=ctk.CTkFont(family=FONTS["LEX_CUST_ENTRY"][0], size=FONTS["LEX_CUST_ENTRY"][1]),
            fg_color=COLORS["SURFACE2"], border_color="#3A3A5C",
            text_color=COLORS["TEXT"], height=60, corner_radius=0,
            border_width=1, wrap="word",
        )
        tb.grid(row=i, column=0, pady=(0, 6), sticky="ew")
        self._definition_fields.append(tb)

    def _validate(self):
        """Validates the input fields and, if valid, adds the custom word to the lexicon."""
        word = self._word_entry.get().strip()
        if not word:
            self._error_label.configure(text="The 'Word' field is required.")
            return

        definitions = [
            tb.get("1.0", "end").strip()
            for tb in self._definition_fields
            if tb.get("1.0", "end").strip()
        ]
        if not definitions:
            self._error_label.configure(text="Enter at least one definition.")
            return

        ok = self.lexicon.add_custom(word, definitions)
        if not ok:
            self._error_label.configure(
                text=f"'{word}' is already in the lexicon."
            )
            return

        self.success_callback()
        self.destroy()