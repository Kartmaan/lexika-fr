"""
main.py
-------
Point d'entrée de Lexika.

Lancement :
    python main.py

Si le fichier french_dict.db est absent du dossier data/,
une fenêtre de setup propose de le télécharger automatiquement
depuis Hugging Face.

Pour utiliser des chemins personnalisés :
    python main.py --db /chemin/vers/mon_dict.db --lexique /chemin/vers/lexique.json
"""

import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Lexika — Dictionnaire français et lexique personnel."
    )
    parser.add_argument(
        "--db",
        default=str(Path(__file__).parent / "data" / "french_dict.db"),
        help="Chemin vers la base SQLite du dictionnaire"
    )
    parser.add_argument(
        "--lexique",
        default=str(Path(__file__).parent / "data" / "lexique.json"),
        help="Chemin vers le fichier JSON du lexique personnel"
    )
    args = parser.parse_args()
    db_path = Path(args.db)

    if not db_path.exists():
        # Dictionnaire absent — proposer le téléchargement
        from ui.setup_window import SetupWindow
        setup = SetupWindow()
        setup.mainloop()
    else:
        # Dictionnaire présent — lancement direct
        from ui.app import App
        try:
            app = App(db_path=db_path, lexique_path=args.lexique)
            app.mainloop()
        except Exception as e:
            print(f"\nErreur au lancement : {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()