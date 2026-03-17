"""
ui/tab_dictionary.py
--------------------
Dictionary tab: word search, definition display, add to lexicon.
"""

import sys
import customtkinter as ctk
from tkinter import StringVar, messagebox

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


def _configure_entry(entry):
    """Fixes Ctrl+A and paste-over-selection for a CTkEntry on Linux."""
    inner = entry._entry

    def ctrl_a(e):
        inner.select_range(0, "end")
        inner.icursor("end")
        return "break"

    def on_paste(e):
        try:
            if inner.selection_present():
                inner.delete("sel.first", "sel.last")
        except Exception:
            pass

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

# Centralized colors
COLOR_ACCENT   = "#4A9EFF"
COLOR_SUCCESS  = "#3DBE7A"
COLOR_ERROR    = "#FF5F5F"
COLOR_NEUTRAL  = "#8A8A9A"
COLOR_SURFACE  = "#1E1E2E"
COLOR_SURFACE2 = "#2A2A3E"
COLOR_TEXT     = "#E8E8F0"
COLOR_TEXT2    = "#A0A0B8"

POS_LABELS = {
    "N":   "Noun",
    "V":   "Verb",
    "ADJ": "Adjective",
    "ADV": "Adverb",
    "PRO": "Pronoun",
    "DET": "Determiner",
    "PRE": "Preposition",
    "CON": "Conjunction",
    "INT": "Interjection",
    "?":   "Undefined",
}


class TabDictionary(ctk.CTkFrame):
    """Main dictionary tab: search and display word definitions."""

    def __init__(self, parent, dictionary, lexicon, **kwargs):
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
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Search bar ---
        search_bar = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=0,
                                  border_width=1, border_color="#2E2E42")
        search_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        search_bar.grid_columnconfigure(0, weight=1)

        self._search_var = StringVar()
        self._search_entry = ctk.CTkEntry(
            search_bar,
            textvariable=self._search_var,
            placeholder_text="Search for a word...",
            font=ctk.CTkFont(family="Georgia", size=15),
            fg_color=COLOR_SURFACE2,
            border_color="#3A3A5C",
            text_color=COLOR_TEXT,
            height=44,
            corner_radius=0,
        )
        self._search_entry.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="ew")
        self._search_entry.bind("<Return>", lambda e: self._run_search())
        _configure_entry(self._search_entry)

        self._btn_search = ctk.CTkButton(
            search_bar,
            text="Search",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color="#3A8EEF",
            text_color="white",
            height=44,
            width=130,
            corner_radius=0,
            command=self._run_search,
        )
        self._btn_search.grid(row=0, column=1, padx=(0, 16), pady=12)

        # --- Results area ---
        results_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=0,
                                     border_width=1, border_color="#2E2E42")
        results_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)

        # Word title
        self._title_label = ctk.CTkLabel(
            results_frame,
            text="",
            font=ctk.CTkFont(family="Georgia", size=26, weight="bold"),
            text_color=COLOR_TEXT,
            anchor="w",
        )
        self._title_label.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))

        # Scrollable definitions area
        self._def_frame = ctk.CTkScrollableFrame(
            results_frame,
            fg_color=COLOR_SURFACE,
            scrollbar_button_color="#3A3A5C",
            scrollbar_button_hover_color=COLOR_ACCENT,
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
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COLOR_NEUTRAL,
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, sticky="w")

        # Button group (right-aligned)
        btn_group = ctk.CTkFrame(footer, fg_color="transparent")
        btn_group.grid(row=0, column=1, sticky="e")

        self._btn_copy = ctk.CTkButton(
            btn_group,
            text="Copy",
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color=COLOR_SURFACE2,
            hover_color="#3A3A5C",
            text_color=COLOR_TEXT,
            height=38,
            width=100,
            corner_radius=0,
            state="disabled",
            command=self._copy_definitions,
        )
        self._btn_copy.pack(side="left", padx=(0, 8))

        self._btn_add = ctk.CTkButton(
            btn_group,
            text="+ Add to lexicon",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#2EAA6A",
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
        word = self._search_var.get().strip()
        if not word:
            return

        self._clear_definitions()
        self._status_label.configure(text="")

        lexemes = self.dictionary.search(word)

        if lexemes:
            self._current_word = word.lower()
            self._current_lexemes = lexemes
            self._show_definitions(word, lexemes)
            self._btn_add.configure(state="normal")
            self._btn_copy.configure(state="normal")
        else:
            self._current_word = None
            self._current_lexemes = None
            self._btn_add.configure(state="disabled")
            self._btn_copy.configure(state="disabled")
            self._show_not_found(word)

    def _format_for_clipboard(self) -> str:
        """Formats the current word and its definitions as plain text for the clipboard."""
        if not self._current_word or not self._current_lexemes:
            return ""

        pos_labels = {
            "N": "Noun", "V": "Verb", "ADJ": "Adjective", "ADV": "Adverb",
            "PRO": "Pronoun", "DET": "Determiner", "PRE": "Preposition",
            "CON": "Conjunction", "INT": "Interjection", "?": "Undefined",
        }

        lines = [self._current_word.capitalize(), ""]

        for lexeme in self._current_lexemes:
            pos = pos_labels.get(lexeme.get("pos", "?"), "?")
            lines.append(f"[{pos}]")

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
                text_color=COLOR_SUCCESS,
            )
            # Reset status after 3 seconds
            self.after(3000, lambda: self._status_label.configure(text=""))
        else:
            self._status_label.configure(
                text="Clipboard unavailable.",
                text_color=COLOR_ERROR,
            )
            _show_clipboard_help()

    def _add_to_lexicon(self):
        if not self._current_word or not self._current_lexemes:
            return

        if self.lexicon.contains(self._current_word):
            self._status_label.configure(
                text=f"'{self._current_word}' is already in your lexicon.",
                text_color=COLOR_NEUTRAL,
            )
            return

        ok = self.lexicon.add_from_dictionary(self._current_word, self._current_lexemes)
        if ok:
            self._status_label.configure(
                text=f"'{ self._current_word}' added to the lexicon.",
                text_color=COLOR_SUCCESS,
            )
            self._btn_add.configure(state="disabled")
        else:
            self._status_label.configure(
                text="Error while adding word.",
                text_color=COLOR_ERROR,
            )

    # ------------------------------------------------------------------
    # Definition display
    # ------------------------------------------------------------------

    def _clear_definitions(self):
        for widget in self._def_frame.winfo_children():
            widget.destroy()
        self._title_label.configure(text="")

    def _show_welcome(self):
        ctk.CTkLabel(
            self._def_frame,
            text="Enter a word in the search field above.",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color=COLOR_NEUTRAL,
            anchor="center",
            justify="center",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(60, 20))

    def _show_not_found(self, word: str):
        self._title_label.configure(text=f"'{word}' not found")

        suggestions = self.dictionary.suggest(word)

        if not suggestions:
            ctk.CTkLabel(
                self._def_frame,
                text="No similar words found. Check the spelling.",
                font=ctk.CTkFont(family="Georgia", size=14),
                text_color=COLOR_ERROR,
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=16, pady=20)
            return

        ctk.CTkLabel(
            self._def_frame,
            text="Did you mean...",
            font=ctk.CTkFont(family="Georgia", size=13),
            text_color=COLOR_NEUTRAL,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        for i, suggestion in enumerate(suggestions):
            ctk.CTkButton(
                self._def_frame,
                text=suggestion,
                font=ctk.CTkFont(family="Georgia", size=14),
                fg_color=COLOR_SURFACE2,
                hover_color="#3A3A5C",
                text_color=COLOR_ACCENT,
                height=34,
                anchor="w",
                corner_radius=0,
                command=lambda w=suggestion: self._search_suggestion(w),
            ).grid(row=i + 1, column=0, sticky="w", padx=16, pady=3)

    def _search_suggestion(self, word: str):
        self._search_var.set(word)
        self._run_search()

    def _show_definitions(self, word: str, lexemes: list):
        self._title_label.configure(text=word.capitalize())

        row = 0
        for lexeme in lexemes:
            pos = lexeme.get("pos", "?")
            pos_label = POS_LABELS.get(pos, pos)

            # POS badge
            ctk.CTkLabel(
                self._def_frame,
                text=f"  {pos_label}  ",
                font=ctk.CTkFont(family="Georgia", size=11, weight="bold"),
                fg_color="#3A3A5C",
                text_color=COLOR_ACCENT,
                corner_radius=0,
                height=22,
            ).grid(row=row, column=0, sticky="w", padx=16, pady=(16, 4))
            row += 1

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
                font=ctk.CTkFont(family="Georgia", size=11, slant="italic"),
                text_color="#7A8AB8",
                anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=left_pad + 20, pady=(4, 0))
            row += 1

        def_row = ctk.CTkFrame(self._def_frame, fg_color="transparent")
        def_row.grid(row=row, column=0, sticky="ew", padx=left_pad, pady=(2, 2))
        def_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            def_row,
            text=prefix,
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=COLOR_ACCENT,
            width=30, anchor="ne",
        ).grid(row=0, column=0, sticky="ne", padx=(0, 6))

        ctk.CTkLabel(
            def_row,
            text=gloss,
            font=ctk.CTkFont(family="Georgia", size=14),
            text_color=COLOR_TEXT,
            wraplength=560, anchor="nw", justify="left",
        ).grid(row=0, column=1, sticky="nw")
        row += 1

        # Usage examples
        for ex in defn.get("exemples", []):
            ctk.CTkLabel(
                self._def_frame,
                text=f"  \"{ex}\"",
                font=ctk.CTkFont(family="Georgia", size=12, slant="italic"),
                text_color=COLOR_TEXT2,
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
            text_color=COLOR_NEUTRAL,
        )