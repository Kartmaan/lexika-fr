"""
main.py
-------
Entry point for Lexika.

Usage:
    python main.py

If french_dict.db is missing from the data/ folder, a setup window
automatically offers to download or import it.

Custom paths:
    python main.py --db /path/to/dict.db --lexicon /path/to/lexicon.json

Author  : Kartmaan
Date    : 2026-03-31
Version : 1.3.0
"""

import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Lexika - French dictionary and personal lexicon."
    )
    parser.add_argument(
        "--db",
        default=str(Path(__file__).parent / "data" / "french_dict.db"),
        help="Path to the SQLite dictionary database"
    )
    parser.add_argument(
        "--lexicon",
        default=str(Path(__file__).parent / "data" / "lexicon.json"),
        help="Path to the personal lexicon JSON file"
    )
    args = parser.parse_args()
    db_path = Path(args.db)

    if not db_path.exists():
        # Dictionary missing - offer download / import
        from ui.setup_window import SetupWindow
        setup = SetupWindow()
        setup.mainloop()
    else:
        # Dictionary present - launch directly
        from ui.app import App
        try:
            app = App(db_path=db_path, lexicon_path=args.lexicon)
            app.mainloop()
        except Exception as e:
            print(f"\nLaunch error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()