"""
ui/app.py
---------
Main window: CustomTkinter setup, TabView, coordination between the three tabs.
"""

import sys
import customtkinter as ctk
from PIL import Image, ImageTk
from pathlib import Path

from core import Dictionary, Lexicon
from ui.tab_dictionary import TabDictionary
from ui.tab_lexicon import TabLexicon
from ui.tab_quiz import TabQuiz
from ui.tab_analyzer import TabAnalyzer

# Assets folder at the project root
ASSETS_DIR = Path(__file__).parent.parent / "assets"

class App(ctk.CTk):
    """Main application window for Lexika."""

    TITLE       = "Lexika - French"
    MIN_WIDTH   = 860
    MIN_HEIGHT  = 600

    def __init__(self, db_path: str | Path, lexicon_path: str | Path):
        super().__init__()

        # --- CustomTkinter configuration ---
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Data ---
        self.dictionary = Dictionary(db_path)
        self.lexicon    = Lexicon(lexicon_path)

        # --- Window ---
        self.title(self.TITLE)
        self.geometry("1060x700")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.configure(fg_color="#12121C")

        # --- Icon (must be applied before building UI) ---
        self._apply_icon()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._quit)

    # ------------------------------------------------------------------
    # Cross-platform icon
    # ------------------------------------------------------------------

    def _apply_icon(self):
        """
        Applies the window icon based on the current platform:
          - Windows : assets/icon.ico
          - macOS   : assets/icon.icns  (fallback: icon.png)
          - Linux   : assets/icon.png

        Fails silently if no icon file is available.
        """
        platform = sys.platform  # 'win32', 'darwin', 'linux'

        # Platform -> preferred file
        if platform == "win32":
            candidates = [ASSETS_DIR / "icon.ico", ASSETS_DIR / "icon.png"]
        elif platform == "darwin":
            candidates = [ASSETS_DIR / "icon.icns", ASSETS_DIR / "icon.png"]
        else:
            candidates = [ASSETS_DIR / "icon.png", ASSETS_DIR / "icon.ico"]

        icon = next((c for c in candidates if c.exists()), None)
        if icon is None:
            return

        try:
            if platform == "win32" and icon.suffix == ".ico":
                # Windows: iconbitmap() handles .ico natively
                self.iconbitmap(str(icon))
            else:
                # Linux / macOS fallback: Pillow -> PhotoImage
                self._icon_from_image(icon)
        except Exception:
            pass  # Silent failure - icon is non-critical

    def _icon_from_image(self, path: Path):
        """
        Loads an image with Pillow and applies it as icon via wm_iconphoto.
        Keeps a reference to prevent garbage collection.
        """
        img = Image.open(path)
        img = img.resize((256, 256), Image.LANCZOS)
        self._icon_ref = ImageTk.PhotoImage(img)
        self.wm_iconphoto(True, self._icon_ref)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title banner
        banner = ctk.CTkFrame(self, fg_color="#1A1A2E", corner_radius=0, height=52)
        banner.grid(row=0, column=0, sticky="ew")
        banner.grid_propagate(False)
        banner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            banner,
            text="Lexika - French",
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
            text_color="#E8E8F0",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=10)

        # Main TabView
        self._tabview = ctk.CTkTabview(
            self,
            fg_color="#1E1E2E",
            segmented_button_fg_color="#1A1A2E",
            segmented_button_selected_color="#4A9EFF",
            segmented_button_selected_hover_color="#3A8EEF",
            segmented_button_unselected_color="#1A1A2E",
            segmented_button_unselected_hover_color="#2A2A3E",
            text_color="#E8E8F0",
            text_color_disabled="#5A5A6A",
            corner_radius=0,
            border_width=0
        )
        # CTkTabview does not support font= directly: configure the internal button
        self._tabview._segmented_button.configure(
            font=ctk.CTkFont(family="Arial", size=14),
            height=44,
            dynamic_resizing=True
        )
        self._tabview.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 16))

        # Create the three tabs
        self._tabview.add("Dictionary")
        self._tabview.add("Lexicon")
        self._tabview.add("Quiz")
        self._tabview.add("Analyzer")

        for name in ["Dictionary", "Lexicon", "Quiz", "Analyzer"]:
            self._tabview._segmented_button._buttons_dict[name].configure(
                width=280, height=44
            )
            self._tabview.tab(name).grid_columnconfigure(0, weight=1)
            self._tabview.tab(name).grid_rowconfigure(0, weight=1)

        # Instantiate tab contents
        self._tab_dict = TabDictionary(
            self._tabview.tab("Dictionary"),
            dictionary=self.dictionary,
            lexicon=self.lexicon,
        )
        self._tab_dict.grid(row=0, column=0, sticky="nsew")

        self._tab_lexicon = TabLexicon(
            self._tabview.tab("Lexicon"),
            lexicon=self.lexicon,
            on_voir_dans_dico=self._navigate_to_dict,
        )
        self._tab_lexicon.grid(row=0, column=0, sticky="nsew")

        self._tab_quiz = TabQuiz(
            self._tabview.tab("Quiz"),
            lexicon=self.lexicon,
        )
        self._tab_quiz.grid(row=0, column=0, sticky="nsew")

        self._tab_analyzer = TabAnalyzer(
            self._tabview.tab("Analyzer"),
            dictionary=self.dictionary,
            on_word_click=self._navigate_to_dict_word,
        )
        self._tab_analyzer.grid(row=0, column=0, sticky="nsew")

        # Cross-tab refresh on tab change
        self._tabview.configure(command=self._on_tab_change)

    # ------------------------------------------------------------------
    # Tab coordination
    # ------------------------------------------------------------------

    def _on_tab_change(self):
        """Synchronizes lexicon-dependent tabs on every tab switch."""
        tab = self._tabview.get()
        if tab == "Lexicon":
            self._tab_lexicon.rafraichir()
        elif tab == "Quiz":
            self._tab_quiz.rafraichir()

    def _navigate_to_dict(self, word: str, entry: dict):
        """
        Callback triggered from the Lexicon tab to display a word
        in the Dictionary tab.
        """
        self._tab_dict.display_from_lexicon(word, entry)
        self._tabview.set("Dictionary")

    def _navigate_to_dict_word(self, word: str):
        """
        Callback triggered from the Analyzer tab.
        Searches the word directly in the Dictionary tab.
        """
        self._tab_dict._search_var.set(word)
        self._tab_dict._run_search()
        self._tabview.set("Dictionary")

    # ------------------------------------------------------------------
    # Clean exit
    # ------------------------------------------------------------------

    def _quit(self):
        self.dictionary.close()
        self.destroy()