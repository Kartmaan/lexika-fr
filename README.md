# French Dict

Dictionnaire français hors-ligne avec lexique personnel et quiz de vocabulaire.

## Prérequis

```bash
pip install customtkinter
```

## Structure du projet

```
french_dict/
├── main.py                  # Point d'entrée
├── core/
│   ├── dictionnaire.py      # Requêtes SQLite
│   └── lexique.py           # Gestion du lexique JSON
├── ui/
│   ├── app.py               # Fenêtre principale
│   ├── tab_dictionnaire.py  # Onglet Dictionnaire
│   ├── tab_lexique.py       # Onglet Lexique
│   └── tab_quiz.py          # Onglet Quiz
└── data/
    ├── french_dict.db       # Base SQLite (à générer)
    └── lexique.json         # Lexique personnel (créé automatiquement)
```

## Préparation de la base de données

Si vous partez du fichier XML source :

```bash
# Étape 1 — XML vers JSON
python xml_to_json.py --input french_dict.xml --output data/french_dict.json --verbose --validate

# Étape 2 — JSON vers SQLite
python json_to_sqlite.py --input data/french_dict.json --output data/french_dict.db --verbose --validate
```

## Lancement

```bash
python main.py
```

Avec des chemins personnalisés :

```bash
python main.py --db /chemin/vers/french_dict.db --lexique /chemin/vers/lexique.json
```

## Fonctionnalités

### Onglet Dictionnaire
- Recherche exacte dans 800 000+ entrées
- Suggestions de mots proches en cas d'introuvable
- Affichage structuré : définitions numérotées, sous-définitions, exemples en italique
- Badges de registre (familier, vieux, littéraire…) et domaine (musique, informatique…)
- Ajout au lexique en un clic

### Onglet Lexique
- Liste alphabétique avec vignettes colorées
- Mots personnalisés (violet) distincts des mots du dictionnaire (bleu)
- Panneau de définition à droite au clic
- Suppression, ajout de mots personnalisés avec formulaire
- Export / Import JSON

### Onglet Quiz
- Session aléatoire sur tous les mots du lexique
- Carte bicolore : face mot (bleu) / face définition (vert)
- Suivi de session : chaque mot n'apparaît qu'une fois par session
- Écran de fin avec option de rejouer
