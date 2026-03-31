"""
ui/tab_quiz.py
--------------
Quiz tab: word/definition flashcard with color change, session tracking.
The card adapts its width (65% of the available frame, clamped between
400 and 1000 px) and scales its fonts proportionally.
"""

import random
import customtkinter as ctk
from core.config import FONTS, COLORS, POS_LABELS, GENDER_LABELS, GENDER_COLORS

COLOR_SURFACE    = "#1E1E2E"
COLOR_SURFACE2   = "#2A2A3E"
COLOR_TEXT       = "#E8E8F0"
COLOR_TEXT2      = "#A0A0B8"
COLOR_NEUTRAL    = "#8A8A9A"
COLOR_ACCENT     = "#4A9EFF"

COLOR_CARD_WORD  = "#1A2A4A"
COLOR_CARD_DEF   = "#1A3A2A"
BORDER_CARD_WORD = "#3A5A8A"
BORDER_CARD_DEF  = "#3A7A5A"

# Card sizing
CARD_RATIO   = 0.65    # fraction of the central frame width
CARD_MIN     = 400     # minimum card width in pixels
CARD_MAX     = 1000    # maximum card width in pixels
RESIZE_DELTA = 20      # minimum pixel change before triggering a rebuild

"""POS_LABELS = {
    "N": "Noun", "V": "Verb", "ADJ": "Adjective", "ADV": "Adverb",
    "PRO": "Pronoun", "DET": "Determiner", "PRE": "Preposition",
    "CON": "Conjunction", "INT": "Interjection", "?": "Undefined",
}"""


def _card_fonts(card_width: int) -> dict:
    """
    Returns a dict of font sizes derived from the card width.
    Three tiers: small / medium / large.
    """
    if card_width < 480:
        return {"word": 26, "subtitle": 11, "body": 11, "btn": 12, "pos": 9}
    elif card_width < 700:
        return {"word": 32, "subtitle": 13, "body": 13, "btn": 14, "pos": 10}
    else:
        return {"word": 42, "subtitle": 15, "body": 15, "btn": 16, "pos": 11}


"""GENDER_LABELS = {"m": "masc.", "f": "fém.", "e": "épicène"}
GENDER_COLORS = {"m": "#4A9EFF", "f": "#FF7EB3", "e": "#A78BFA"}"""

class TabQuiz(ctk.CTkFrame):
    """Vocabulary quiz tab."""

    def __init__(self, parent, lexicon, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.lexicon = lexicon

        self._session_words: list[str] = []
        self._seen_words:    list[str] = []
        self._current_word:  str | None = None
        self._show_word_side: bool = True

        # Track card width to avoid unnecessary rebuilds
        self._card_width: int = 560
        self._last_frame_width: int = 0

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="Vocabulary Quiz",
            font=ctk.CTkFont(family="Georgia", size=18, weight="bold"),
            text_color=COLOR_TEXT,
        ).pack(side="left", padx=16, pady=12)

        self._progress_label = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(family=FONTS["QUIZ_LABEL"][0], size=FONTS["QUIZ_LABEL"][1]),
            text_color=COLOR_NEUTRAL,
        )
        self._progress_label.pack(side="left", padx=4, pady=12)

        self._btn_restart = ctk.CTkButton(
            header, text="Restart",
            font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1]),
            fg_color=COLOR_SURFACE2, hover_color="#3A3A5C",
            text_color=COLOR_ACCENT,
            height=34, corner_radius=0,
            command=self._start_session,
        )
        self._btn_restart.pack(side="right", padx=12, pady=10)

        # Central area
        self._central_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._central_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self._central_frame.grid_columnconfigure(0, weight=1)
        self._central_frame.grid_rowconfigure(0, weight=1)

        # Bind resize event to adapt card width
        self._central_frame.bind("<Configure>", self._on_frame_resize)

        self._show_waiting_screen()

    # ------------------------------------------------------------------
    # Responsive card sizing
    # ------------------------------------------------------------------

    def _on_frame_resize(self, event):
        """Reacts to frame resize; rebuilds the card only when needed."""
        frame_width = event.width
        if abs(frame_width - self._last_frame_width) < RESIZE_DELTA:
            return  # change too small — skip rebuild

        self._last_frame_width = frame_width
        new_width = max(CARD_MIN, min(CARD_MAX, int(frame_width * CARD_RATIO)))

        if abs(new_width - self._card_width) < RESIZE_DELTA:
            return  # card width unchanged — skip rebuild

        self._card_width = new_width

        # Rebuild the active card if one is displayed
        if self._current_word:
            self._show_card()

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------

    def _clear_frame(self):
        for w in self._central_frame.winfo_children():
            w.destroy()

    def _show_waiting_screen(self):
        """Displayed when the lexicon is empty or before starting."""
        self._clear_frame()

        frame = ctk.CTkFrame(
            self._central_frame, fg_color=COLOR_SURFACE, corner_radius=0
        )
        frame.grid(row=0, column=0)

        is_empty = self.lexicon.is_empty()

        ctk.CTkLabel(
            frame, text="?",
            font=ctk.CTkFont(size=48),
            text_color=COLOR_TEXT,
        ).pack(pady=(32, 8), padx=48)

        msg = (
            "Your lexicon is empty.\nAdd words from the Dictionary tab."
            if is_empty else
            f"Ready to practice?\n{self.lexicon.word_count()} word(s) available."
        )
        ctk.CTkLabel(
            frame, text=msg,
            font=ctk.CTkFont(family=FONTS["QUIZ_WELCOME"][0], size=FONTS["QUIZ_WELCOME"][1]),
            text_color=COLOR_TEXT2, justify="center",
        ).pack(pady=(0, 16), padx=48)

        if not is_empty:
            ctk.CTkButton(
                frame, text="Start quiz",
                font=ctk.CTkFont(family=FONTS["QUIZ_START"][0], size=FONTS["QUIZ_START"][1], weight=FONTS["QUIZ_START"][2]),
                fg_color=COLOR_ACCENT, hover_color="#3A8EEF",
                text_color="white", height=44, width=200, corner_radius=0,
                command=self._start_session,
            ).pack(pady=(0, 32))

    def _show_session_end(self):
        """Displayed when all words have been reviewed."""
        self._clear_frame()
        self._progress_label.configure(text="")

        frame = ctk.CTkFrame(
            self._central_frame, fg_color=COLOR_SURFACE, corner_radius=0
        )
        frame.grid(row=0, column=0)

        ctk.CTkLabel(
            frame, text="Well done!",
            font=ctk.CTkFont(family="Georgia", size=32, weight="bold"),
            text_color=COLOR_TEXT,
        ).pack(pady=(32, 8), padx=64)

        ctk.CTkLabel(
            frame,
            text=f"You have reviewed all\n{len(self._seen_words)} words in your lexicon.",
            font=ctk.CTkFont(family=FONTS["QUIZ_LABEL"][0], size=FONTS["QUIZ_START"][1]),
            text_color=COLOR_TEXT, justify="center",
        ).pack(pady=(0, 16))

        ctk.CTkButton(
            frame, text="Play again",
            font=ctk.CTkFont(family=FONTS["QUIZ_BTN"][0], size=FONTS["QUIZ_BTN"][1], weight=FONTS["QUIZ_BTN"][2]),
            fg_color=COLOR_ACCENT, hover_color="#3A8EEF",
            text_color="white", height=44, width=160, corner_radius=0,
            command=self._start_session,
        ).pack(pady=(0, 32))

    def _show_card(self):
        """Displays the adaptive flashcard for the current word."""
        self._clear_frame()

        entry = self.lexicon.get(self._current_word)
        if not entry:
            self._next_word()
            return

        fonts = _card_fonts(self._card_width)
        wrap  = max(200, self._card_width - 120)   # wraplength for definition text

        # Center the card by applying symmetric horizontal padding to the wrapper.
        # The card itself fills the wrapper (sticky="ew") and grows freely in height.
        margin = max(0, (self._last_frame_width - self._card_width) // 2)
        wrapper = ctk.CTkFrame(self._central_frame, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="ew", padx=(margin, margin))
        wrapper.grid_columnconfigure(0, weight=1)

        # --- Card ---
        card_color  = COLOR_CARD_WORD  if self._show_word_side else COLOR_CARD_DEF
        card_border = BORDER_CARD_WORD if self._show_word_side else BORDER_CARD_DEF

        self._card = ctk.CTkFrame(
            wrapper,
            fg_color=card_color, corner_radius=0,
            border_width=2, border_color=card_border,
        )
        # sticky="ew" lets the card fill the wrapper width;
        # no grid_propagate(False) so height grows freely with content.
        self._card.grid(row=0, column=0, pady=(0, 24), sticky="ew")
        self._card.grid_columnconfigure(0, weight=1)

        if self._show_word_side:
            self._build_word_face(self._card, fonts)
        else:
            self._build_definition_face(self._card, entry, fonts, wrap)

        # --- Next word button ---
        btn_width = max(160, min(240, self._card_width // 3))
        ctk.CTkButton(
            wrapper, text="Next word  ->",
            font=ctk.CTkFont(family=FONTS["QUIZ_BTN"][0], size=FONTS["QUIZ_BTN"][1], weight=FONTS["QUIZ_BTN"][2]),
            fg_color=COLOR_SURFACE, hover_color="#3A3A5C",
            border_color="#3A3A5C", border_width=1,
            text_color=COLOR_TEXT,
            height=max(36, fonts["btn"] * 3),
            width=btn_width,
            corner_radius=0,
            command=self._next_word,
        ).grid(row=1, column=0)

    # ------------------------------------------------------------------
    # Card faces
    # ------------------------------------------------------------------

    def _build_word_face(self, parent, fonts: dict):
        """Word side: shows the word and a 'See the answer' button."""
        pad = max(20, self._card_width // 16)

        ctk.CTkLabel(
            parent, text="What is the definition of...",
            font=ctk.CTkFont(family=FONTS["QUIZ_WELCOME"][0], size=FONTS["QUIZ_WELCOME"][1], slant=FONTS["QUIZ_WELCOME"][3]),
            text_color="#7A9ABE",
        ).grid(row=0, column=0, pady=(pad, 4), padx=pad)

        ctk.CTkLabel(
            parent, text=self._current_word.capitalize(),
            font=ctk.CTkFont(family=FONTS["QUIZ_WORD"][0], size=FONTS["QUIZ_WORD"][1], weight=FONTS["QUIZ_WORD"][2]),
            text_color="#A8D0FF",
        ).grid(row=1, column=0, pady=(4, pad), padx=pad)

        btn_w = max(140, self._card_width // 4)
        ctk.CTkButton(
            parent, text="See the answer",
            font=ctk.CTkFont(family=FONTS["QUIZ_BTN"][0], size=FONTS["QUIZ_BTN"][1], weight=FONTS["QUIZ_BTN"][2]),
            fg_color="#2A4A7A", hover_color="#3A5A8A",
            text_color="#A8D0FF",
            height=max(36, fonts["btn"] * 3),
            width=btn_w,
            corner_radius=0,
            command=self._flip_card,
        ).grid(row=2, column=0, pady=(0, pad))

    def _build_definition_face(self, parent, entry: dict, fonts: dict, wrap: int):
        """Definition side: shows definitions and a 'See the word' button."""
        pad = max(16, self._card_width // 18)

        ctk.CTkLabel(
            parent, text=self._current_word.capitalize(),
            font=ctk.CTkFont(family="Arial", size=fonts["word"] // 2 + 8, weight="bold"),
            text_color="#80C8A0",
        ).grid(row=0, column=0, pady=(pad, 4), padx=pad, sticky="w")

        ctk.CTkFrame(parent, height=1, fg_color="#3A7A5A").grid(
            row=1, column=0, sticky="ew", padx=pad, pady=(0, 8)
        )

        row = 2
        for lexeme in entry.get("lexemes", []):
            pos_label = POS_LABELS.get(lexeme.get("pos", "?"), "?")

            gender      = lexeme.get("gender")
            show_gender = (lexeme.get("pos") == "N" and gender in GENDER_LABELS)

            badge_row = ctk.CTkFrame(parent, fg_color="transparent")
            badge_row.grid(row=row, column=0, sticky="w", padx=pad, pady=(4, 2))
            row += 1

            ctk.CTkLabel(
                badge_row, text=f"  {pos_label}  ",
                font=ctk.CTkFont(family="Arial", size=fonts["pos"], weight="bold"),
                fg_color="#2A5A3A", text_color="#80C8A0",
                corner_radius=0, height=20,
            ).pack(side="left", padx=(0, 4))

            if show_gender:
                ctk.CTkLabel(
                    badge_row,
                    text=f"  {GENDER_LABELS[gender]}  ",
                    font=ctk.CTkFont(family="Arial", size=fonts["pos"], weight="bold"),
                    fg_color="#1A2A1A", text_color=GENDER_COLORS[gender],
                    corner_radius=0, height=20,
                ).pack(side="left")

            for i, defn in enumerate(lexeme.get("definitions", [])[:3], 1):
                gloss = defn.get("gloss", "")
                def_row = ctk.CTkFrame(parent, fg_color="transparent")
                def_row.grid(row=row, column=0, sticky="ew", padx=pad, pady=(2, 2))
                def_row.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    def_row, text=f"{i}.",
                    font=ctk.CTkFont(family="Arial", size=fonts["body"], weight="bold"),
                    text_color="#80C8A0", width=24, anchor="ne",
                ).grid(row=0, column=0, sticky="ne", padx=(0, 6))

                ctk.CTkLabel(
                    def_row, text=gloss,
                    font=ctk.CTkFont(family="Arial", size=fonts["body"]),
                    text_color="#C8EED8",
                    wraplength=wrap, anchor="nw", justify="left",
                ).grid(row=0, column=1, sticky="nw")
                row += 1

        btn_w = max(140, self._card_width // 4)
        ctk.CTkButton(
            parent, text="See the word",
            font=ctk.CTkFont(family=FONTS["QUIZ_BTN"][0], size=FONTS["QUIZ_BTN"][1], weight=FONTS["QUIZ_BTN"][2]),
            fg_color="#2A5A3A", hover_color="#3A6A4A",
            text_color="#80C8A0",
            height=max(36, fonts["btn"] * 3),
            width=btn_w,
            corner_radius=0,
            command=self._flip_card,
        ).grid(row=row, column=0, pady=(12, pad))

    # ------------------------------------------------------------------
    # Session logic
    # ------------------------------------------------------------------

    def _start_session(self):
        if self.lexicon.is_empty():
            self._show_waiting_screen()
            return

        words = self.lexicon.words()
        random.shuffle(words)
        self._session_words = words
        self._seen_words = []
        self._next_word()

    def _next_word(self):
        if not self._session_words:
            self._show_session_end()
            return

        self._current_word = self._session_words.pop(0)
        self._seen_words.append(self._current_word)
        self._show_word_side = True
        self._update_progress()
        self._show_card()

    def _flip_card(self):
        self._show_word_side = not self._show_word_side
        self._show_card()

    def _update_progress(self):
        total = len(self._seen_words) + len(self._session_words)
        self._progress_label.configure(text=f"{len(self._seen_words)} / {total}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rafraichir(self):
        """Called when the lexicon changes - resets the screen."""
        if self.lexicon.is_empty() or not self._current_word:
            self._show_waiting_screen()