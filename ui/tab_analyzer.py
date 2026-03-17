"""
ui/tab_analyzer.py
------------------
Analyzer tab: multi-criteria word filtering from the dictionary database.

Filters (all optional, cumulative):
  - length      : exact number of letters
  - start_with  : prefix
  - end_with    : suffix
  - contains    : letters the word must include
  - not_contain : letters the word must exclude
  - nth_letters : letter at a specific position (dynamic rows)
  - anagram     : the word must be an anagram of given letters
  - no_comp     : exclude compound words (default: on)

Results are displayed as clickable tiles that open the Dictionary tab.
"""

import threading
import customtkinter as ctk
from tkinter import StringVar, IntVar, BooleanVar

COLOR_ACCENT   = "#4A9EFF"
COLOR_SUCCESS  = "#3DBE7A"
COLOR_ERROR    = "#FF5F5F"
COLOR_NEUTRAL  = "#8A8A9A"
COLOR_SURFACE  = "#1E1E2E"
COLOR_SURFACE2 = "#2A2A3E"
COLOR_SURFACE3 = "#14141F"
COLOR_TEXT     = "#E8E8F0"
COLOR_TEXT2    = "#A0A0B8"

MAX_RESULTS = 500   # hard cap on displayed words

def _bind_mousewheel(scrollable_frame):
    """Enables mouse wheel scrolling on a CTkScrollableFrame."""
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

class TabAnalyzer(ctk.CTkFrame):
    """Multi-criteria word filtering tab."""

    def __init__(self, parent, dictionary, on_word_click=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.dictionary = dictionary
        self.on_word_click = on_word_click   # callback(word) -> opens Dictionary tab

        # nth_letters dynamic rows: list of (pos_var, letter_var, row_frame)
        self._nth_rows: list[tuple[StringVar, StringVar, ctk.CTkFrame]] = []

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)   # left: filters
        self.grid_columnconfigure(1, weight=1)   # right: results
        self.grid_rowconfigure(0, weight=1)

        self._build_filter_panel()
        self._build_results_panel()

    # ---- Left column: filter panel -----------------------------------

    def _build_filter_panel(self):
        left = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE3, corner_radius=0,
            border_width=1, border_color="#2E2E42", width=280
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(20, 6), pady=20)
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        # Header
        ctk.CTkLabel(
            left,
            text="Filters",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        # Scrollable filters area
        filters_scroll = ctk.CTkScrollableFrame(
            left, fg_color="transparent",
            scrollbar_button_color="#3A3A5C",
            scrollbar_button_hover_color=COLOR_ACCENT,
        )
        filters_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        filters_scroll.grid_columnconfigure(0, weight=1)
        _bind_mousewheel(filters_scroll)

        self._build_filter_fields(filters_scroll)

        # Buttons at the bottom
        btn_area = ctk.CTkFrame(left, fg_color="transparent")
        btn_area.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 14))
        btn_area.grid_columnconfigure(0, weight=1)
        btn_area.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_area, text="Reset",
            font=ctk.CTkFont(family="Arial", size=12),
            fg_color=COLOR_SURFACE2, hover_color="#3A3A5C",
            text_color=COLOR_TEXT2,
            height=34, corner_radius=0,
            command=self._reset_filters,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            btn_area, text="Search",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            fg_color=COLOR_ACCENT, hover_color="#3A8EEF",
            text_color="white",
            height=34, corner_radius=0,
            command=self._run_analysis,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _build_filter_fields(self, parent):
        """Creates all filter input widgets inside the scrollable area."""
        row = 0

        # Helper: section label
        def section(text, r):
            ctk.CTkLabel(
                parent, text=text,
                font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
                text_color=COLOR_NEUTRAL, anchor="w",
            ).grid(row=r, column=0, sticky="w", padx=14, pady=(10, 2))
            return r + 1

        # Helper: small entry
        def entry_field(var, placeholder, r, width=None):
            e = ctk.CTkEntry(
                parent, textvariable=var,
                placeholder_text=placeholder,
                font=ctk.CTkFont(family="Arial", size=13),
                fg_color=COLOR_SURFACE2, border_color="#3A3A5C",
                text_color=COLOR_TEXT, height=32, corner_radius=0,
            )
            if width:
                e.configure(width=width)
            e.grid(row=r, column=0, sticky="ew", padx=14, pady=(0, 2))
            e.bind("<Return>", lambda ev: self._run_analysis())
            return r + 1

        # --- Length ---
        row = section("LENGTH  (exact number of letters)", row)
        self._var_length = StringVar()
        # Create the entry manually to add numeric-only validation
        length_entry = ctk.CTkEntry(
            parent,
            textvariable=self._var_length,
            placeholder_text="e.g.  7",
            font=ctk.CTkFont(family="Georgia", size=13),
            fg_color=COLOR_SURFACE2, border_color="#3A3A5C",
            text_color=COLOR_TEXT, height=32, corner_radius=0,
        )
        length_entry.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 2))
        length_entry.bind("<Return>", lambda ev: self._run_analysis())
        # Allow only digit keys (and control keys like Backspace, Delete, arrows)
        def _numeric_only(event):
            if event.keysym in ("BackSpace", "Delete", "Left", "Right",
                                "Home", "End", "Tab"):
                return  # allow
            if not event.char.isdigit():
                return "break"  # block non-digit
        length_entry._entry.bind("<KeyPress>", _numeric_only)
        row += 1

        # --- Starts with ---
        row = section("STARTS WITH", row)
        self._var_start = StringVar()
        row = entry_field(self._var_start, "e.g.  gr", row)

        # --- Ends with ---
        row = section("ENDS WITH", row)
        self._var_end = StringVar()
        row = entry_field(self._var_end, "e.g.  it", row)

        # --- Contains ---
        row = section("CONTAINS", row)
        self._var_contains = StringVar()
        row = entry_field(self._var_contains, "e.g.  au  or  a u", row)

        # --- Does not contain ---
        row = section("NOT CONTAIN", row)
        self._var_not_contain = StringVar()
        row = entry_field(self._var_not_contain, "e.g.  bx  or  b x", row)

        # --- Anagram ---
        row = section("ANAGRAM", row)
        self._var_anagram = StringVar()
        row = entry_field(self._var_anagram, "e.g.  carte  or  c a r t e", row)

        # --- Nth letters ---
        row = section("LETTER AT POSITION  (pos + letter)", row)

        self._nth_container = ctk.CTkFrame(parent, fg_color="transparent")
        self._nth_container.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 4))
        self._nth_container.grid_columnconfigure(0, weight=1)
        row += 1

        self._nth_rows_frame = ctk.CTkFrame(self._nth_container, fg_color="transparent")
        self._nth_rows_frame.grid(row=0, column=0, sticky="ew")
        self._nth_rows_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            self._nth_container,
            text="+ Add position",
            font=ctk.CTkFont(family="Arial", size=11),
            fg_color=COLOR_SURFACE2, hover_color="#3A3A5C",
            text_color=COLOR_ACCENT,
            height=26, corner_radius=0,
            command=self._add_nth_row,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Add one row by default
        self._add_nth_row()

        # --- No compounds switch ---
        sep = ctk.CTkFrame(parent, height=1, fg_color="#2E2E42")
        sep.grid(row=row, column=0, sticky="ew", padx=14, pady=(10, 8))
        row += 1

        switch_row = ctk.CTkFrame(parent, fg_color="transparent")
        switch_row.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 8))
        switch_row.grid_columnconfigure(0, weight=1)
        row += 1

        self._var_no_comp = BooleanVar(value=True)
        ctk.CTkLabel(
            switch_row, text="Exclude compound words",
            font=ctk.CTkFont(family="Arial", size=12),
            text_color=COLOR_TEXT2, anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkSwitch(
            switch_row,
            text="",
            variable=self._var_no_comp,
            onvalue=True, offvalue=False,
            progress_color=COLOR_ACCENT,
            width=40,
        ).grid(row=0, column=1, sticky="e")

    def _add_nth_row(self):
        """Adds a new [position] [letter] row in the nth_letters section."""
        idx = len(self._nth_rows)

        frame = ctk.CTkFrame(self._nth_rows_frame, fg_color="transparent")
        frame.grid(row=idx, column=0, sticky="ew", pady=2)
        frame.grid_columnconfigure(1, weight=1)

        pos_var = StringVar()
        letter_var = StringVar()

        # Position field (narrow)
        ctk.CTkLabel(
            frame, text="Pos",
            font=ctk.CTkFont(family="Arial", size=11),
            text_color=COLOR_NEUTRAL, width=24,
        ).grid(row=0, column=0, padx=(0, 4))

        ctk.CTkEntry(
            frame, textvariable=pos_var,
            font=ctk.CTkFont(family="Arial", size=13),
            fg_color=COLOR_SURFACE2, border_color="#3A3A5C",
            text_color=COLOR_TEXT, height=28, width=48, corner_radius=0,
        ).grid(row=0, column=1, padx=(0, 6))

        # Letter field (narrow)
        ctk.CTkLabel(
            frame, text="=",
            font=ctk.CTkFont(family="Arial", size=13),
            text_color=COLOR_NEUTRAL,
        ).grid(row=0, column=2, padx=(0, 4))

        ctk.CTkEntry(
            frame, textvariable=letter_var,
            font=ctk.CTkFont(family="Arial", size=13),
            fg_color=COLOR_SURFACE2, border_color="#3A3A5C",
            text_color=COLOR_TEXT, height=28, width=48, corner_radius=0,
        ).grid(row=0, column=3, padx=(0, 6))

        # Remove button
        remove_btn = ctk.CTkButton(
            frame, text="x",
            font=ctk.CTkFont(family="Arial", size=11),
            fg_color="#3A1A1A", hover_color="#5A2A2A",
            text_color=COLOR_ERROR,
            height=28, width=28, corner_radius=0,
            command=lambda f=frame, pv=pos_var, lv=letter_var: self._remove_nth_row(f, pv, lv),
        )
        remove_btn.grid(row=0, column=4)

        self._nth_rows.append((pos_var, letter_var, frame))

    def _remove_nth_row(self, frame, pos_var, letter_var):
        """Removes a nth_letters row."""
        self._nth_rows = [
            (pv, lv, f) for pv, lv, f in self._nth_rows
            if f is not frame
        ]
        frame.destroy()

    # ---- Right column: results panel ---------------------------------

    def _build_results_panel(self):
        right = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE, corner_radius=0,
            border_width=1, border_color="#2E2E42"
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 20), pady=20)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # Results header
        header = ctk.CTkFrame(right, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        header.grid_columnconfigure(0, weight=1)

        self._result_label = ctk.CTkLabel(
            header,
            text="Results will appear here after a search.",
            font=ctk.CTkFont(family="Arial", size=13),
            text_color=COLOR_NEUTRAL, anchor="w",
        )
        self._result_label.grid(row=0, column=0, sticky="w")

        self._spinner_label = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(family="Arial", size=12),
            text_color=COLOR_ACCENT,
        )
        self._spinner_label.grid(row=0, column=1, sticky="e")

        # Scrollable results area
        self._results_frame = ctk.CTkScrollableFrame(
            right, fg_color=COLOR_SURFACE,
            scrollbar_button_color="#3A3A5C",
            scrollbar_button_hover_color=COLOR_ACCENT,
            corner_radius=0,
        )
        self._results_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        _bind_mousewheel(self._results_frame)

        #self._show_idle_message()

    def _show_idle_message(self):
        """More helpful message ?
        """
        for w in self._results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._results_frame,
            text="Set one or more filters on the left, then click Search.",
            font=ctk.CTkFont(family="Arial", size=13),
            text_color=COLOR_NEUTRAL, justify="left", anchor="w",
        ).pack(anchor="w", padx=16, pady=20)

    # ------------------------------------------------------------------
    # Filter logic
    # ------------------------------------------------------------------

    def _collect_filters(self) -> dict:
        """Reads all filter fields and returns a clean params dict."""
        params = {}

        # Length
        raw_len = self._var_length.get().strip()
        if raw_len:
            try:
                params["length"] = int(raw_len)
            except ValueError:
                pass

        # Start / end
        s = self._var_start.get().strip().lower()
        if s:
            params["start_with"] = s

        e = self._var_end.get().strip().lower()
        if e:
            params["end_with"] = e

        # Contains: accept continuous "au" or spaced "a u" — split by character
        raw_c = self._var_contains.get().replace(" ", "").lower()
        if raw_c:
            params["contains"] = [l for l in raw_c if l.isalpha()]

        # Not contain: accept continuous "bx" or spaced "b x" — split by character
        raw_nc = self._var_not_contain.get().replace(" ", "").lower()
        if raw_nc:
            params["not_contain"] = [l for l in raw_nc if l.isalpha()]

        # Anagram: accept continuous "carte" or spaced "c a r t e" — split by character
        raw_ag = self._var_anagram.get().replace(" ", "").lower()
        if raw_ag:
            params["anagram"] = [l for l in raw_ag if l.isalpha()]

        # Nth letters
        nth = []
        for pos_var, letter_var, _ in self._nth_rows:
            pos_s = pos_var.get().strip()
            letter_s = letter_var.get().strip().lower()
            if pos_s and letter_s:
                try:
                    nth.append([int(pos_s), letter_s[0]])
                except ValueError:
                    pass
        if nth:
            params["nth_letters"] = nth

        params["no_comp"] = self._var_no_comp.get()
        params["limit"] = MAX_RESULTS

        return params

    def _has_any_filter(self, params: dict) -> bool:
        """Returns True if at least one meaningful filter is set."""
        meaningful = {"length", "start_with", "end_with", "contains",
                      "not_contain", "anagram", "nth_letters"}
        return bool(meaningful & set(params.keys()))

    def _run_analysis(self):
        """Validates filters, then runs the search in a background thread."""
        params = self._collect_filters()

        if not self._has_any_filter(params):
            self._show_error("Please set at least one filter before searching.")
            return

        # Disable search while running
        self._spinner_label.configure(text="Searching...")
        self._result_label.configure(text="", text_color=COLOR_NEUTRAL)

        for w in self._results_frame.winfo_children():
            w.destroy()

        thread = threading.Thread(
            target=self._search_thread, args=(params,), daemon=True
        )
        thread.start()

    def _search_thread(self, params: dict):
        """Runs analyze() in a background thread, then schedules UI update."""
        try:
            words, truncated = self.dictionary.analyze(**params)
            self.after(0, self._display_results, words, truncated)
        except Exception as e:
            self.after(0, self._show_error, f"Search error: {e}")

    # ------------------------------------------------------------------
    # Results display
    # ------------------------------------------------------------------

    def _display_results(self, words: list[str], truncated: bool):
        self._spinner_label.configure(text="")

        for w in self._results_frame.winfo_children():
            w.destroy()

        if not words:
            self._result_label.configure(
                text="No words found matching these criteria.",
                text_color=COLOR_NEUTRAL,
            )
            ctk.CTkLabel(
                self._results_frame,
                text="No results. Try relaxing some filters.",
                font=ctk.CTkFont(family="Arial", size=13),
                text_color=COLOR_NEUTRAL, anchor="w",
            ).pack(anchor="w", padx=16, pady=20)
            return

        count_text = f"{len(words)} word{'s' if len(words) > 1 else ''} found"
        if truncated:
            count_text += f"  (limited to {MAX_RESULTS} — refine your search)"
        self._result_label.configure(text=count_text, text_color=COLOR_SUCCESS)

        # Render word tiles in a wrapping grid
        # We use a regular Frame inside the scrollable area and pack rows
        tile_container = ctk.CTkFrame(self._results_frame, fg_color="transparent")
        tile_container.pack(fill="both", expand=True, padx=8, pady=8)

        COLS = 5   # tiles per row
        for i, word in enumerate(words):
            r, c = divmod(i, COLS)
            btn = ctk.CTkButton(
                tile_container,
                text=word.capitalize(),
                font=ctk.CTkFont(family="Arial", size=13),
                fg_color=COLOR_SURFACE2,
                hover_color="#3A3A5C",
                text_color=COLOR_ACCENT,
                height=34, width=120,
                corner_radius=0,
                command=lambda w=word: self._on_tile_click(w),
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="ew")

        # Make columns equal width
        for c in range(COLS):
            tile_container.grid_columnconfigure(c, weight=1)

    def _on_tile_click(self, word: str):
        """Navigates to the Dictionary tab to show the selected word."""
        if self.on_word_click:
            self.on_word_click(word)

    def _show_error(self, message: str):
        self._spinner_label.configure(text="")
        self._result_label.configure(text=message, text_color=COLOR_ERROR)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def _reset_filters(self):
        self._var_length.set("")
        self._var_start.set("")
        self._var_end.set("")
        self._var_contains.set("")
        self._var_not_contain.set("")
        self._var_anagram.set("")
        self._var_no_comp.set(True)

        # Clear nth rows and add one fresh empty row
        for _, _, frame in self._nth_rows:
            frame.destroy()
        self._nth_rows.clear()
        self._add_nth_row()

        # Reset results panel
        self._result_label.configure(
            text="Results will appear here after a search.",
            text_color=COLOR_NEUTRAL,
        )
        #self._show_idle_message()