"""
ui/setup_window.py
------------------
First-launch window displayed when french_dict.db is missing.
Offers the user two options:
  - Download the dictionary from Hugging Face
  - Import a compatible .db file from disk

Launches the main application once the dictionary is available.
"""

import shutil
import sqlite3
import threading
import urllib.request
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from core.config import FONTS, COLORS

DB_URL  = "https://huggingface.co/datasets/Kartmaan/french-dictionary/resolve/main/french_dict.db"
DB_DEST = Path(__file__).parent.parent / "data" / "french_dict.db"

# Minimum columns expected in the 'mots' table
REQUIRED_COLUMNS = {"forme", "pos", "definitions", "gender"}

# ---------------------------------------------------------------------------
# Database validation
# ---------------------------------------------------------------------------

def _validate_db(path: Path) -> tuple[bool, str]:
    """
    Checks whether a file is a valid Lexika-compatible dictionary.
    Returns (valid: bool, message: str).
    """
    if path.suffix.lower() != ".db":
        return False, "File must have the .db extension."

    if path.stat().st_size < 1024:
        return False, "File is too small to be a valid dictionary."

    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()

        # Check for the 'mots' table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mots'"
        )
        if not cursor.fetchone():
            conn.close()
            return False, "Table 'mots' not found - this file is not compatible."

        # Check required columns
        cursor.execute("PRAGMA table_info(mots)")
        columns = {row[1] for row in cursor.fetchall()}
        missing = REQUIRED_COLUMNS - columns
        if missing:
            conn.close()
            return (
                False,
                f"Missing columns: {', '.join(sorted(missing))}.\n"
                "This file is not compatible with Lexika."
            )

        # Check that data is present
        cursor.execute("SELECT COUNT(*) FROM mots")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            return False, "The 'mots' table is empty."

        return True, f"Valid file - {count:,} entries found."

    except sqlite3.DatabaseError:
        return False, "Invalid or corrupted SQLite file."
    except Exception as e:
        return False, f"Validation error: {e}"


# ---------------------------------------------------------------------------
# Setup window
# ---------------------------------------------------------------------------

class SetupWindow(ctk.CTk):
    """Setup window: download or import the dictionary on first launch."""

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Lexika - Setup")
        self.geometry("540x400")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["BG"])

        self._download_in_progress = False
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        frame = ctk.CTkFrame(
            self, fg_color=COLORS["SURFACE"],
            corner_radius=0, border_width=1, border_color="#2E2E42"
        )
        frame.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        frame.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            frame,
            text="Welcome to Lexika",
            font=ctk.CTkFont(family="Georgia", size=24, weight="bold"),
            text_color=COLORS["TEXT"],
        ).grid(row=0, column=0, pady=(24, 4))

        # Message
        ctk.CTkLabel(
            frame,
            text="The dictionary needs to be downloaded or imported from your disk.",
            font=ctk.CTkFont(family=FONTS["WELCOME_LABEL"][0], size=FONTS["WELCOME_LABEL"][1]),
            text_color=COLORS["NEUTRAL"], justify="center",
        ).grid(row=1, column=0, padx=24, pady=(0, 20))

        # Progress bar (hidden by default)
        self._progress_bar = ctk.CTkProgressBar(
            frame, width=420, height=10, corner_radius=0,
            fg_color=COLORS["SURFACE2"], progress_color=COLORS["ACCENT"],
        )
        self._progress_bar.set(0)
        self._progress_bar.grid(row=2, column=0, padx=32, pady=(0, 6))
        self._progress_bar.grid_remove()

        # Status label
        self._status_label = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(family="Georgia", size=12),
            text_color=COLORS["NEUTRAL"], wraplength=460, justify="center",
        )
        self._status_label.grid(row=3, column=0, padx=16, pady=(0, 16))

        # Separator
        ctk.CTkFrame(frame, height=1, fg_color="#2E2E42").grid(
            row=4, column=0, sticky="ew", padx=24, pady=(0, 20)
        )

        # --- Download block ---
        dl_block = ctk.CTkFrame(frame, fg_color="transparent")
        dl_block.grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 10))
        dl_block.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dl_block,
            text="From Internet (Hugging Face, ~280 MB)",
            font=ctk.CTkFont(family=FONTS["STATUS_LABEL"][0], size=FONTS["STATUS_LABEL"][1]),
            text_color=COLORS["NEUTRAL"], anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._btn_download = ctk.CTkButton(
            dl_block, text="Download",
            font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1], weight=FONTS["BTN"][2]),
            fg_color=COLORS["ACCENT"], hover_color="#3A8EEF",
            text_color="white", height=38, width=160, corner_radius=0,
            command=self._start_download,
        )
        self._btn_download.grid(row=0, column=1, padx=(12, 0))

        # --- Import block ---
        imp_block = ctk.CTkFrame(frame, fg_color="transparent")
        imp_block.grid(row=6, column=0, sticky="ew", padx=24, pady=(0, 10))
        imp_block.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            imp_block,
            text="From disk (compatible .db file)",
            font=ctk.CTkFont(family=FONTS["STATUS_LABEL"][0], size=FONTS["STATUS_LABEL"][1]),
            text_color=COLORS["NEUTRAL"], anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._btn_import = ctk.CTkButton(
            imp_block, text="Import",
            font=ctk.CTkFont(family=FONTS["BTN"][0], size=FONTS["BTN"][1], weight=FONTS["BTN"][2]),
            fg_color="#5A4E8A", hover_color="#6A5E9A",
            text_color="white", height=38, width=160, corner_radius=0,
            command=self._import_db,
        )
        self._btn_import.grid(row=0, column=1, padx=(12, 0))

        # --- Quit button ---
        self._btn_quit = ctk.CTkButton(
            frame, text="Quit",
            font=ctk.CTkFont(family="Georgia", size=12),
            fg_color="transparent", hover_color="#2A2A3E",
            text_color=COLORS["NEUTRAL"], height=30, corner_radius=0,
            command=self.destroy,
        )
        self._btn_quit.grid(row=7, column=0, pady=(4, 20))

    # ------------------------------------------------------------------
    # Import from disk
    # ------------------------------------------------------------------

    def _import_db(self):
        path = filedialog.askopenfilename(
            title="Select dictionary file",
            filetypes=[("SQLite database", "*.db"), ("All files", "*.*")],
        )
        if not path:
            return

        path = Path(path)
        self._status_label.configure(text="Verifying file...", text_color=COLORS["NEUTRAL"])
        self.update_idletasks()

        valid, message = _validate_db(path)

        if not valid:
            self._status_label.configure(
                text=f"Invalid file: {message}", text_color=COLORS["ERROR"]
            )
            return

        try:
            DB_DEST.parent.mkdir(parents=True, exist_ok=True)
            self._status_label.configure(text="Copying...", text_color=COLORS["NEUTRAL"])
            self.update_idletasks()
            shutil.copy2(path, DB_DEST)
        except Exception as e:
            self._status_label.configure(
                text=f"Copy error: {e}", text_color=COLORS["ERROR"]
            )
            return

        self._status_label.configure(text=f"OK  {message}", text_color=COLORS["SUCCESS"])
        self._btn_import.configure(state="disabled", text="OK  Imported", fg_color=COLORS["SUCCESS"])
        self._btn_download.configure(state="disabled")
        self._btn_quit.configure(state="disabled")
        self.after(1400, self._launch_app)

    # ------------------------------------------------------------------
    # Download from Hugging Face
    # ------------------------------------------------------------------

    def _start_download(self):
        if self._download_in_progress:
            return

        self._download_in_progress = True
        self._btn_download.configure(state="disabled", text="Downloading...")
        self._btn_import.configure(state="disabled")
        self._btn_quit.configure(state="disabled")
        self._progress_bar.grid()
        self._progress_bar.configure(mode="indeterminate")
        self._progress_bar.start()
        self._status_label.configure(
            text="Connecting to Hugging Face...", text_color=COLORS["NEUTRAL"]
        )

        threading.Thread(target=self._download, daemon=True).start()

    def _download(self):
        """Runs the download in a separate thread to keep the UI responsive."""
        try:
            DB_DEST.parent.mkdir(parents=True, exist_ok=True)
            tmp = DB_DEST.with_suffix(".tmp")

            def hook(count, block_size, total_size):
                if total_size > 0:
                    downloaded = count * block_size
                    progress = min(downloaded / total_size, 1.0)
                    mb_dl  = downloaded  / 1_048_576
                    mb_tot = total_size  / 1_048_576
                    self.after(0, self._update_progress, progress, mb_dl, mb_tot)

            urllib.request.urlretrieve(DB_URL, tmp, reporthook=hook)
            tmp.rename(DB_DEST)
            self.after(0, self._download_success)

        except Exception as e:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            self.after(0, self._download_failed, str(e))

    def _update_progress(self, progress: float, mb_dl: float, mb_tot: float):
        self._progress_bar.stop()
        self._progress_bar.configure(mode="determinate")
        self._progress_bar.set(progress)
        self._status_label.configure(
            text=f"{mb_dl:.1f} MB / {mb_tot:.1f} MB  ({progress * 100:.0f}%)",
            text_color=COLORS["NEUTRAL"],
        )

    def _download_success(self):
        self._progress_bar.set(1.0)
        self._status_label.configure(
            text="Download complete - launching Lexika...", text_color=COLORS["SUCCESS"]
        )
        self._btn_download.configure(
            text="OK  Done", fg_color=COLORS["SUCCESS"], hover_color=COLORS["SUCCESS"]
        )
        self.after(1200, self._launch_app)

    def _download_failed(self, error: str):
        self._download_in_progress = False
        self._progress_bar.stop()
        self._progress_bar.set(0)
        msg = error[:70] + "..." if len(error) > 70 else error
        self._status_label.configure(text=f"Error: {msg}", text_color=COLORS["ERROR"])
        self._btn_download.configure(
            state="normal", text="Retry",
            fg_color=COLORS["ERROR"], hover_color="#CC4444"
        )
        self._btn_import.configure(state="normal")
        self._btn_quit.configure(state="normal")

    # ------------------------------------------------------------------
    # Launch main app
    # ------------------------------------------------------------------

    def _launch_app(self):
        self.destroy()
        from ui.app import App
        app = App(
            db_path=DB_DEST,
            lexicon_path=DB_DEST.parent / "lexicon.json"
        )
        app.mainloop()