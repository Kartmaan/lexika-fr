# Lexika — Dictionnaire français hors-ligne

Lexika est une application de bureau Python permettant de consulter un dictionnaire français complet en local, de constituer un lexique personnel de vocabulaire et de le réviser sous forme de quiz interactif.

---

## Aperçu

---

## Fonctionnalités principales

- **Dictionnaire hors-ligne** de plus de 800 000 entrées françaises, incluant les formes conjuguées
- **Définitions structurées** : sous-définitions, exemples d'usage, registres (familier, littéraire, vieux...) et domaines (musique, informatique...)
- **Suggestions intelligentes** en cas de mot introuvable, avec prise en charge des accents manquants (`element` → `élément`)
- **Lexique personnel** pour sauvegarder les mots qui vous intéressent
- **Mots personnalisés** : ajoutez vos propres définitions pour des termes absents du dictionnaire
- **Quiz de vocabulaire** pour réviser les mots de votre lexique
- **Import / Export** du lexique au format JSON
- **Interface sombre moderne** construite avec CustomTkinter
- **Fenêtre redimensionnable** avec contenu adaptatif

---

## Prérequis

- Python 3.10 ou supérieur
- Les dépendances listées dans `requirements.txt`

```bash
pip install -r requirements.txt
```

`requirements.txt` :
```
customtkinter
pillow
```

---

## Installation et premier lancement

### 1. Cloner le dépôt

```bash
git clone https://github.com/Kartmaan/lexika-fr.git
cd lexika-fr
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancer l'application

```bash
python main.py
```

Au premier lancement, si le fichier `data/french_dict.db` est absent, une fenêtre de configuration s'affiche automatiquement et vous propose deux options :

- **Télécharger** le dictionnaire depuis Hugging Face (~270 Mo)
- **Importer** un fichier `.db` compatible déjà présent sur votre disque

Le fichier est vérifié automatiquement avant utilisation (extension, structure SQLite, présence des données).

---

## Structure du projet

```
lexika-fr/
├── main.py                  # Point d'entrée
├── requirements.txt
├── assets/
│   ├── icon.png             # Icône Linux
│   ├── icon.ico             # Icône Windows
│   └── icon.icns            # Icône macOS
├── core/
│   ├── dictionnaire.py      # Requêtes SQLite + suggestions
│   └── lexique.py           # Gestion du lexique JSON
├── ui/
│   ├── app.py               # Fenêtre principale et onglets
│   ├── setup_window.py      # Fenêtre de premier lancement
│   ├── tab_dictionnaire.py  # Onglet Dictionnaire
│   ├── tab_lexique.py       # Onglet Lexique
│   └── tab_quiz.py          # Onglet Quiz
└── data/
    ├── french_dict.db       # Base SQLite (générée au setup)
    └── lexique.json         # Lexique personnel (créé automatiquement)
```

---

## Onglet Dictionnaire

L'onglet principal de l'application.

**Recherche**
- Saisissez un mot dans le champ de recherche et validez avec le bouton ou la touche `Entrée`
- La recherche est insensible à la casse

**Affichage des résultats**
- Les définitions sont regroupées par partie du discours (Nom, Verbe, Adjectif...) avec un badge de couleur
- Chaque définition est numérotée et peut contenir :
  - Des sous-définitions hiérarchisées
  - Des exemples d'usage en italique
  - Des étiquettes de registre *(familier)*, de sens *[figuré]* ou de domaine *‹musique›*

**Mot introuvable**
- Si le mot n'existe pas dans le dictionnaire, Lexika propose automatiquement des mots proches
- La recherche approximative prend en charge les **accents manquants** : taper `element` suggère `élément`, taper `enchevetre` suggère `enchevêtré`
- Cliquer sur une suggestion lance directement sa définition

**Ajout au lexique**
- Un bouton **Ajouter au lexique** est disponible sous chaque résultat
- Si le mot est déjà présent dans le lexique, un message vous en informe

---

## Onglet Lexique

Le lexique personnel, organisé en deux colonnes.

**Colonne gauche — liste des mots**
- Les mots enregistrés apparaissent par ordre alphabétique sous forme de vignettes
- Les mots issus du dictionnaire apparaissent en bleu
- Les mots personnalisés apparaissent en violet

**Colonne droite — définitions**
- Cliquer sur une vignette affiche immédiatement la définition complète dans la colonne de droite
- Un bouton **Voir dans le dictionnaire** permet de naviguer vers l'onglet Dictionnaire pour consulter l'entrée originale (disponible uniquement pour les mots issus du dictionnaire)

**Gestion du lexique**
- **Supprimer** un mot du lexique via le bouton dédié
- **Ajouter un mot personnalisé** : ouvre un formulaire permettant de saisir un mot et une ou plusieurs définitions libres — utile pour les termes techniques, jargons ou néologismes absents du dictionnaire
- **Exporter** le lexique vers un fichier `.json` de votre choix
- **Importer** un lexique préalablement exporté — les mots déjà présents sont conservés, les nouveaux sont fusionnés

---

## Onglet Quiz

Un outil de révision du vocabulaire enregistré dans le lexique.

**Déroulement**
- Le quiz ne peut démarrer que si le lexique contient au moins un mot
- Les mots sont tirés dans un ordre aléatoire en début de session
- Chaque mot n'apparaît qu'une seule fois par session de quiz

**La carte**
- La carte affiche d'abord le mot à définir sur fond bleu
- Le bouton **Voir la réponse** retourne la carte : elle passe sur fond vert et affiche la ou les définitions
- Le bouton **Voir le mot** permet de revenir à la face initiale
- Le bouton **Mot suivant** passe au mot suivant de la session

**Fin de session**
- Lorsque tous les mots ont été parcourus, un écran de fin s'affiche avec le nombre de mots révisés
- Un bouton **Rejouer** lance une nouvelle session avec un ordre aléatoire différent

---

## Source du dictionnaire

Le dictionnaire est dérivé de **WiktionaryX**, une ressource lexicale structurée issue du Wiktionnaire français, produite par **Franck Sajous**, ingénieur de recherche CNRS et enseignant en Sciences du Langage à l'Université de Toulouse.

Source originale : http://redac.univ-tlse2.fr/lexiques/wiktionaryx.html

Le fichier `french_dict.db` est hébergé séparément sur Hugging Face (licence CC BY-SA 4.0) :
👉 https://huggingface.co/datasets/Kartmaan/french-dictionary

---

## Licences

| Composant | Licence |
|---|---|
| Code source (ce dépôt) | MIT |
| Base de données `french_dict.db` | CC BY-SA 4.0 (dérivé du Wiktionnaire) |

---