"""
ui/tab_dictionary.py
--------------------
Dictionary tab: word search, definition display, add to lexicon.
"""

import customtkinter as ctk
from tkinter import StringVar, messagebox

from core.config import FONTS, COLORS, POS_LABELS, GENDER_LABELS, GENDER_COLORS

def _bind_mousewheel(scrollable_frame):
    """Enables mouse wheel scrolling on a CTkScrollableFrame (Linux + Windows)."""
    canvas = scrollable_frame._parent_canvas # access the internal canvas of the CTkScrollableFrame

    def scroll(delta):
        """Scrolls the canvas by a given delta (positive or negative integer)

        Args:
            delta (_type_): Number of units to scroll. Positive for down, negative for up.
        """
        canvas.yview_scroll(delta, "units")

    def on_enter(_):
        """Binds mouse wheel events when the mouse enters the frame.

        Args:
            _ (_type_): The event object (not used).
        """
        scrollable_frame.bind_all("<Button-4>",   lambda e: scroll(-1))
        scrollable_frame.bind_all("<Button-5>",   lambda e: scroll(1))
        scrollable_frame.bind_all("<MouseWheel>", lambda e: scroll(int(-1 * e.delta / 120)))

    def on_leave(_):
        """Unbinds mouse wheel events when the mouse leaves the frame.
        
        Args:
            _ (_type_): The event object (not used).
        """

        scrollable_frame.unbind_all("<Button-4>")
        scrollable_frame.unbind_all("<Button-5>")
        scrollable_frame.unbind_all("<MouseWheel>")

    # Bind enter and leave events to the scrollable frame to manage mouse wheel bindings
    scrollable_frame.bind("<Enter>", on_enter, add="+")
    scrollable_frame.bind("<Leave>", on_leave, add="+")


def _configure_entry(entry):
    """Fixes Ctrl+A and paste-over-selection for a CTkEntry on Linux.
    On Linux, Ctrl+A does not select all text by default, and pasting 
    while text is selected does not replace it. This function binds 
    custom handlers to implement these expected behaviors."""
    inner = entry._entry

    def ctrl_a(e):
        """Selects all text in the entry when Ctrl+A is pressed."""
        inner.select_range(0, "end")
        inner.icursor("end")
        return "break"

    def on_paste(e):
        """When pasting, if there is a selection, delete it first 
        to replace it with the clipboard content."""
        try:
            if inner.selection_present():
                inner.delete("sel.first", "sel.last")
        except Exception:
            pass

    # Bind the handlers to the internal entry widget
    inner.bind("<Control-a>", ctrl_a)
    inner.bind("<Control-A>", ctrl_a)
    inner.bind("<<Paste>>", on_paste, add="+")

def _copy_to_clipboard(widget, text: str) -> bool:
    """
    Copies text to the system clipboard.

    Strategy (most to least portable):
      1. tkinter built-in clipboard (no external dependency)
      2. pyperclip (fallback)

    Returns True on success, False on failure.
    """
    # --- Attempt 1: tkinter native clipboard ---
    try:
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.update()  # required on some platforms to persist after window close
        return True
    except Exception:
        pass

    # --- Attempt 2: pyperclip ---
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        pass  # pyperclip not installed
    except Exception:
        pass  # pyperclip installed but no clipboard mechanism found

    return False

def _show_clipboard_help():
    """
    Displays a help dialog when clipboard access fails on Linux,
    with the packages to install depending on the display server.
    """
    msg = (
        "Clipboard access failed.\n\n"
        "On Linux, a clipboard utility must be installed:\n\n"
        "  X11 (most desktop environments):\n"
        "    sudo apt install xclip\n"
        "    or: sudo apt install xsel\n\n"
        "  Wayland (GNOME, KDE on Wayland):\n"
        "    sudo apt install wl-clipboard\n\n"
        "After installation, restart the application."
    )
    messagebox.showinfo("Clipboard unavailable", msg)

class TabDictionary(ctk.CTkFrame):
    """Main dictionary tab: search and display word definitions."""

    def __init__(self, parent, dictionary, lexicon, **kwargs):
        """Constructor for the TabDictionary frame.

        Args:
            parent (_type_): The parent widget (the tab frame).
            dictionary (_type_): The dictionary object to query for word definitions.
            lexicon (_type_): The lexicon object to manage saved words.
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.dictionary = dictionary
        self.lexicon = lexicon
        self._current_word: str | None = None
        self._current_lexemes: list | None = None
        self._copy_available: bool = True  # set to False after a clipboard failure

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Constructs the UI components of the dictionary tab."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Search bar ---
        search_bar = ctk.CTkFrame(self, fg_color=COLORS["SURFACE"], corner_radius=0,
                                  border_width=1, border_color="#2E2E42")
        search_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        search_bar.grid_columnconfigure(0, weight=1)

        self._search_var = StringVar() # holds the current search query and is linked to the search entry
        self._search_entry = ctk.CTkEntry(
            search_bar,
            textvariable=self._search_var,
            placeholder_text="Search for a word...",
            font=ctk.CTkFont(family=FONTS["SEARCH_BAR"][0], size=FONTS["SEARCH_BAR"][1]),
            fg_color=COLORS["SURFACE2"],
            border_color=COLORS["DICT_ENTRY_BORDER"],
            text_color=COLORS["TEXT"],
            height=44,
            corner_radius=0,
        )
        self._search_entry.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="ew")
        self._search_entry.bind("<Return>", lambda e: self._run_search())
        _configure_entry(self._search_entry)

        # --- Search button ---
        self._btn_search = ctk.CTkButton(
            search_bar,
            text="Search",
            font=ctk.CTkFont(family=FONTS["SEARCH_BTN"][0], size=FONTS["SEARCH_BTN"][1], weight=FONTS["SEARCH_BTN"][2]),
            fg_color=COLORS["ACCENT"],
            hover_color=COLORS["HOVER"],
            text_color="white",
            height=44,
            width=130,
            corner_radius=0,
            command=self._run_search,
        )
        self._btn_search.grid(row=0, column=1, padx=(0, 16), pady=12)

        # --- Results area ---
        results_frame = ctk.CTkFrame(self, fg_color=COLORS["SURFACE"], corner_radius=0,
                                     border_width=1, border_color="#2E2E42")
        results_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)

        # Word title
        self._title_label = ctk.CTkLabel(
            results_frame,
            text="",
            font=ctk.CTkFont(family=FONTS["WORD_TITLE"][0], size=FONTS["WORD_TITLE"][1], weight=FONTS["WORD_TITLE"][2]),
            text_color=COLORS["TEXT"],
            anchor="w",
        )
        self._title_label.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))

        # Scrollable definitions area
        self._def_frame = ctk.CTkScrollableFrame(
            results_frame,
            fg_color=COLORS["SURFACE"],
            scrollbar_button_color=COLORS["SCROLLBAR"],
            scrollbar_button_hover_color=COLORS["ACCENT"],
            corner_radius=0,
        )
        self._def_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._def_frame.grid_columnconfigure(0, weight=1)
        _bind_mousewheel(self._def_frame)

        # Welcome message
        self._show_welcome()

        # --- Footer: button + status message ---
        footer = ctk.CTkFrame(results_frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 16))
        footer.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(family=FONTS["STATUS_LABEL"][0], size=FONTS["STATUS_LABEL"][1]),
            text_color=COLORS["NEUTRAL"],
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, sticky="w")

        # Button group (right-aligned)
        btn_group = ctk.CTkFrame(footer, fg_color="transparent")
        btn_group.grid(row=0, column=1, sticky="e")

        # --- Copy button ---
        self._btn_copy = ctk.CTkButton(
            btn_group,
            text="Copy",
            font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1]),
            fg_color=COLORS["SURFACE2"],
            hover_color=COLORS["DICT_COPY_BTN_HOVER"],
            text_color=COLORS["TEXT"],
            height=38,
            width=100,
            corner_radius=0,
            state="disabled",
            command=self._copy_definitions,
        )
        self._btn_copy.pack(side="left", padx=(0, 8))

        # --- Add to lexicon button ---
        self._btn_add = ctk.CTkButton(
            btn_group,
            text="+ Add to lexicon",
            font=ctk.CTkFont(family=FONTS["ADD_BTN"][0], size=FONTS["ADD_BTN"][1], weight=FONTS["ADD_BTN"][2]),
            fg_color=COLORS["SUCCESS"],
            hover_color=COLORS["DICT_ADD_BTN_HOVER"],
            text_color="white",
            height=38,
            width=180,
            corner_radius=0,
            state="disabled",
            command=self._add_to_lexicon,
        )
        self._btn_add.pack(side="left")

    # ------------------------------------------------------------------
    # Search logic
    # ------------------------------------------------------------------

    def _run_search(self):
        """Executes a search query using the dictionary and updates 
        the UI with results or suggestions."""
        word = self._search_var.get().strip()
        if not word:
            return

        self._clear_definitions() # clear previous results/suggestions
        self._status_label.configure(text="") # clear status messages

        lexemes = self.dictionary.search(word)

        if lexemes: # valid word with definitions found
            self._current_word = word.lower()
            self._current_lexemes = lexemes
            self._show_definitions(word, lexemes)
            self._btn_add.configure(state="normal")
            self._btn_copy.configure(state="normal")
        else: # no exact match found - show suggestions and disable buttons
            self._current_word = None
            self._current_lexemes = None
            self._btn_add.configure(state="disabled")
            self._btn_copy.configure(state="disabled")
            self._show_not_found(word)

    # ------------------------------------------------------------------
    # Copy logic (clipboard)
    # ------------------------------------------------------------------

    def _format_for_clipboard(self) -> str:
        """Formats the current word and its definitions as plain text for the clipboard."""
        if not self._current_word or not self._current_lexemes:
            return ""

        # Format: Word
        #         [POS — Gender (for nouns)] 
        #           1. Definition (tags)
        #              "Example sentence"
        lines = [self._current_word.capitalize(), ""]

        # Iterate through lexemes to format each definition with its
        for lexeme in self._current_lexemes:
            pos    = lexeme.get("pos", "?")
            pos_fr = POS_LABELS.get(pos, "?")
            gender = lexeme.get("gender")

            if pos == "N" and gender in GENDER_LABELS:
                lines.append(f"[{pos_fr} — {GENDER_LABELS[gender]}]")
            else:
                lines.append(f"[{pos_fr}]")

            for i, defn in enumerate(lexeme.get("definitions", []), 1):
                gloss = defn.get("gloss", "")
                # Contextual tags
                tags = []
                if defn.get("register"): tags.append(f"({defn['register']})")
                if defn.get("semantic"):  tags.append(f"[{defn['semantic']}]")
                if defn.get("domain"):    tags.append(f"<{defn['domain']}>")
                tag_str = " ".join(tags)

                prefix = f"{tag_str} " if tag_str else ""
                lines.append(f"  {i}. {prefix}{gloss}")

                for ex in defn.get("exemples", []):
                    lines.append(f'     "{ex}"')

                for j, sub in enumerate(defn.get("sous_definitions", []), 1):
                    sub_gloss = sub.get("gloss", "")
                    lines.append(f"     {i}.{j}. {sub_gloss}")

            lines.append("")

        return "\n".join(lines).rstrip()

    def _copy_definitions(self):
        """Copies the current word and its definitions to the clipboard."""
        text = self._format_for_clipboard()
        if not text:
            return

        success = _copy_to_clipboard(self, text)

        if success:
            self._status_label.configure(
                text="Copied to clipboard.",
                text_color=COLORS["SUCCESS"],
            )
            # Reset status after 3 seconds
            self.after(3000, lambda: self._status_label.configure(text=""))
        else:
            self._status_label.configure(
                text="Clipboard unavailable.",
                text_color=COLORS["ERROR"],
            )
            _show_clipboard_help()

    def _add_to_lexicon(self):
        """Adds the current word and its lexemes to the user's lexicon."""
        if not self._current_word or not self._current_lexemes:
            return

        if self.lexicon.contains(self._current_word):
            self._status_label.configure(
                text=f"'{self._current_word.capitalize()}' is already in your lexicon.",
                text_color=COLORS["NEUTRAL"],
            )
            return

        ok = self.lexicon.add_from_dictionary(self._current_word, self._current_lexemes)
        if ok:
            self._status_label.configure(
                text=f"'{self._current_word.capitalize()}' added to the lexicon.",
                text_color=COLORS["SUCCESS"],
            )
            self._btn_add.configure(state="disabled")
        else:
            self._status_label.configure(
                text="Error while adding word.",
                text_color=COLORS["ERROR"],
            )

    # ------------------------------------------------------------------
    # Definition display
    # ------------------------------------------------------------------

    def _clear_definitions(self):
        """Clears the definitions area and resets the title label."""
        for widget in self._def_frame.winfo_children():
            widget.destroy()
        self._title_label.configure(text="")

    def _show_welcome(self):
        """Displays a welcome message when no search has been made."""
        ctk.CTkLabel(
            self._def_frame,
            text="Enter a word in the search field above.",
            font=ctk.CTkFont(family=FONTS["WELCOME_LABEL"][0], size=FONTS["WELCOME_LABEL"][1]),
            text_color=COLORS["NEUTRAL"],
            anchor="center",
            justify="center",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(60, 20))

    def _show_not_found(self, word: str):
        """Displays a 'not found' message and suggestions when a search yields no results."""
        self._title_label.configure(text=f"'{word}' not found")

        suggestions = self.dictionary.suggest(word)

        if not suggestions:
            ctk.CTkLabel(
                self._def_frame,
                text="No similar words found. Check the spelling.",
                font=ctk.CTkFont(family=FONTS["WELCOME_LABEL"][0], size=FONTS["WELCOME_LABEL"][1]),
                text_color=COLORS["ERROR"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=16, pady=20)
            return

        ctk.CTkLabel(
            self._def_frame,
            text="Did you mean...",
            font=ctk.CTkFont(family=FONTS["WELCOME_LABEL"][0], size=FONTS["WELCOME_LABEL"][1]),
            text_color=COLORS["NEUTRAL"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        for i, suggestion in enumerate(suggestions):
            ctk.CTkButton(
                self._def_frame,
                text=suggestion,
                font=ctk.CTkFont(family=FONTS["SUGGESTIONS"][0], size=FONTS["SUGGESTIONS"][1]),
                fg_color=COLORS["DICT_SUGGEST_FRAME"],
                hover_color=COLORS["DICT_SUGGEST_FRAME_HOVER"],
                text_color=COLORS["DICT_SUGGEST_TEXT"],
                height=34,
                anchor="w",
                corner_radius=0,
                command=lambda w=suggestion: self._search_suggestion(w),
            ).grid(row=i + 1, column=0, sticky="w", padx=16, pady=3)

    def _search_suggestion(self, word: str):
        """When a suggestion button is clicked, populate the search bar with 
        the suggestion and run the search."""
        self._search_var.set(word)
        self._run_search()

    def _show_definitions(self, word: str, lexemes: list):
        """Displays the definitions of a word in the definitions area."""
        self._title_label.configure(text=word.capitalize())

        row = 0
        for lexeme in lexemes:
            pos = lexeme.get("pos", "?")
            pos_label = POS_LABELS.get(pos, pos)

            # POS badge + optional gender badge (for nouns)
            gender     = lexeme.get("gender")   # 'm', 'f', 'e', or None
            show_gender = (pos == "N" and gender in GENDER_LABELS)

            badge_row = ctk.CTkFrame(self._def_frame, fg_color="transparent")
            badge_row.grid(row=row, column=0, sticky="w", padx=16, pady=(16, 4))
            row += 1

            ctk.CTkLabel(
                badge_row,
                text=f"  {pos_label}  ",
                font=ctk.CTkFont(family=FONTS["BADGE"][0], size=FONTS["BADGE"][1], weight=FONTS["BADGE"][2]),
                fg_color=COLORS["BADGE"],
                text_color=COLORS["ACCENT"],
                corner_radius=0,
                height=22,
            ).pack(side="left", padx=(0, 4))

            if show_gender:
                gender_text  = GENDER_LABELS[gender]
                gender_color = GENDER_COLORS[gender]
                ctk.CTkLabel(
                    badge_row,
                    text=f"  {gender_text}  ",
                    font=ctk.CTkFont(family=FONTS["BADGE"][0], size=FONTS["BADGE"][1], weight=FONTS["BADGE"][2]),
                    fg_color=COLORS["BADGE"],
                    text_color=gender_color,
                    corner_radius=0,
                    height=22,
                ).pack(side="left")

            for i, defn in enumerate(lexeme.get("definitions", []), 1):
                row = self._show_definition_item(row, i, defn, level=0)

        # End separator
        ctk.CTkFrame(self._def_frame, height=1, fg_color="#3A3A5C").grid(
            row=row, column=0, sticky="ew", padx=16, pady=(12, 8)
        )

    def _show_definition_item(self, row: int, number, defn: dict, level: int) -> int:
        """Displays one definition (top-level or sub-level) and returns the next row index."""
        left_pad = 16 + level * 24

        gloss    = defn.get("gloss", "")
        register = defn.get("register")
        semantic = defn.get("semantic")
        domain   = defn.get("domain")
        prefix   = f"{number}." if level == 0 else f"  {number}."

        # Contextual tags (register, semantic, domain)
        tags = []
        if register: tags.append(f"({register})")
        if semantic:  tags.append(f"[{semantic}]")
        if domain:    tags.append(f"<{domain}>")
        tag_str = "  ".join(tags)

        if tag_str:
            ctk.CTkLabel(
                self._def_frame,
                text=tag_str,
                font=ctk.CTkFont(family=FONTS["TAG"][0], size=FONTS["TAG"][1], slant=FONTS["TAG"][3]),
                text_color=COLORS["TEXT_TAG"],
                anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=left_pad + 20, pady=(4, 0))
            row += 1

        def_row = ctk.CTkFrame(self._def_frame, fg_color="transparent")
        def_row.grid(row=row, column=0, sticky="ew", padx=left_pad, pady=(2, 2))
        def_row.grid_columnconfigure(1, weight=1)

        # Prefix number
        ctk.CTkLabel(
            def_row,
            text=prefix,
            font=ctk.CTkFont(family=FONTS["PREFIX_DEF"][0], size=FONTS["PREFIX_DEF"][1], weight=FONTS["PREFIX_DEF"][2]),
            text_color=COLORS["ACCENT"],
            width=30, anchor="ne",
        ).grid(row=0, column=0, sticky="ne", padx=(0, 6))

        # Definition
        ctk.CTkLabel(
            def_row,
            text=gloss,
            font=ctk.CTkFont(family=FONTS["DEFINITION"][0], size=FONTS["DEFINITION"][1]),
            text_color=COLORS["TEXT"],
            wraplength=560, anchor="nw", justify="left",
        ).grid(row=0, column=1, sticky="nw")
        row += 1

        # Usage examples
        for ex in defn.get("exemples", []):
            ctk.CTkLabel(
                self._def_frame,
                text=f"  \"{ex}\"",
                font=ctk.CTkFont(family=FONTS["EXAMPLE"][0], size=FONTS["EXAMPLE"][1], slant=FONTS["EXAMPLE"][3]),
                text_color=COLORS["TEXT2"],
                wraplength=540, anchor="w", justify="left",
            ).grid(row=row, column=0, sticky="w", padx=left_pad + 20, pady=(1, 1))
            row += 1

        # Sub-definitions
        for j, sub_def in enumerate(defn.get("sous_definitions", []), 1):
            row = self._show_definition_item(row, f"{number}.{j}", sub_def, level=1)

        return row

    # ------------------------------------------------------------------
    # Public API - called from the Lexicon tab
    # ------------------------------------------------------------------

    def display_from_lexicon(self, word: str, entry: dict):
        """Displays a word and its definitions sourced from the lexicon (no SQL query)."""
        self._clear_definitions()
        self._status_label.configure(text="")
        self._search_var.set(word)
        self._current_word = word
        self._current_lexemes = entry.get("lexemes", [])
        self._show_definitions(word, self._current_lexemes)

        self._btn_add.configure(state="disabled")
        self._btn_copy.configure(state="normal")
        self._status_label.configure(
            text=f"'{word}' is already in your lexicon.",
            text_color=COLORS["NEUTRAL"],
        )