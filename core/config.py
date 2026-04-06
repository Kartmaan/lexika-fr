"""
core/config.py
------------------
This module defines the global visual identity and grammatical mapping 
used across the User Interface (UI) and data processing layers. 

It contains:
- FONTS: A comprehensive mapping of UI components (titles, buttons, 
  lexicon lists, etc.) to their respective font families, sizes, and styles.
- POS_LABELS: Mapping of Part-of-Speech (POS) abbreviations (e.g., 'N', 'V') 
  to their full French descriptive labels.
- GENDER_LABELS: Definitions for grammatical genders (Masculine, Feminine, 
  Epicene) used for noun categorization.
- COLORS & GENDER_COLORS: A standardized color palette (Hex codes) for 
  the dark theme surface levels and gender-coded visual cues.

The gender data implemented here supports the enriched 'french_dict.db' 
schema, facilitating the cross-referencing of French nouns with 
grammatical gender markers.
"""
# ----------------------------------------------------------------
#                               FONTS
# ----------------------------------------------------------------
_DEFAULT_FONT = "Arial"

FONTS = {
    # KEY : [Font, size, weight, slant]
    # App / Global
    "TITLE" : ["Georgia", 22, "bold", "roman"],
    "BTN" : [_DEFAULT_FONT, 13, "normal", "roman"],
    "TABS" : [_DEFAULT_FONT, 16, "normal", "roman"],
    "BADGE" : [_DEFAULT_FONT, 13, "normal", "roman"],
    "TAG" : [_DEFAULT_FONT, 11, "normal", "italic"],
    "PREFIX_DEF" : [_DEFAULT_FONT, 14, "bold", "roman"],
    "DEFINITION" : [_DEFAULT_FONT, 14, "normal", "roman"],
    "EXAMPLE" : [_DEFAULT_FONT, 12, "normal", "italic"],

    # Dictionary tab
    "SEARCH_BAR" : [_DEFAULT_FONT, 20, "normal", "roman"],
    "WELCOME_LABEL" : [_DEFAULT_FONT, 14, "normal", "roman"],
    "WORD_TITLE" : [_DEFAULT_FONT, 26, "bold", "roman"],
    "SUGGESTIONS" : [_DEFAULT_FONT, 15, "normal", "roman"],
    "STATUS_LABEL" : [_DEFAULT_FONT, 12, "normal", "roman"],
    "SEARCH_BTN" : [_DEFAULT_FONT, 15, "normal", "roman"],
    "ADD_BTN" : [_DEFAULT_FONT, 13, "bold", "roman"],
    
    # Lexicon tab
    "LEX_TITLE" : [_DEFAULT_FONT, 18, "bold", "roman"],
    "LEX_COUNT" : [_DEFAULT_FONT, 12, "normal", "roman"],
    "LEX_BTN" : [_DEFAULT_FONT, 13, "normal", "roman"],
    "LEX_DEF_TITLE" : [_DEFAULT_FONT, 22, "bold", "roman"],
    "LEX_LABEL" : [_DEFAULT_FONT, 13, "normal", "roman"],
    "LEX_WRD_LIST" : [_DEFAULT_FONT, 15, "normal", "roman"],
    "LEX_CUST_TITLE" : [_DEFAULT_FONT, 18, "bold", "roman"],
    "LEX_CUST_CAT" : [_DEFAULT_FONT, 14, "bold", "roman"],
    "LEX_CUST_ENTRY" : [_DEFAULT_FONT, 15, "normal", "roman"],

    # Quiz tab
    "QUIZ_LABEL" : [_DEFAULT_FONT, 14, "normal", "roman"],
    "QUIZ_WELCOME" : [_DEFAULT_FONT, 16, "normal", "roman"],
    "QUIZ_START" : [_DEFAULT_FONT, 16, "bold", "roman"],
    "QUIZ_BTN" : [_DEFAULT_FONT, 18, "bold", "roman"],
    "QUIZ_WORD" : [_DEFAULT_FONT, 35, "bold", "roman"],

    # Analyzer tab
    "ANALYZER_TITLE" : [_DEFAULT_FONT, 16, "bold", "roman"],
    "ANALYZER_HELP" : [_DEFAULT_FONT, 11, "normal", "roman"],
    "ANALYZER_ENTRY" : [_DEFAULT_FONT, 14, "normal", "roman"],
    "ANALYZER_MINI_BTN" : [_DEFAULT_FONT, 11, "normal", "roman"],
    "ANALYZER_STATUS" : [_DEFAULT_FONT, 15, "normal", "roman"],
    "ANALYZER_RESULT" : [_DEFAULT_FONT, 13, "normal", "roman"],
}
# FONTS["ANALYZER_TITLE"][0]
# ----------------------------------------------------------------
#                               LABELS
# ----------------------------------------------------------------
POS_LABELS = {
    "N":   "Nom",
    "V":   "Verbe",
    "ADJ": "Adjectif",
    "ADV": "Adverbe",
    "PRO": "Pronom",
    "DET": "Déterminant",
    "PRE": "Préposition",
    "CON": "Conjonction",
    "INT": "Interjection",
    "?":   "Non défini",
}

GENDER_LABELS = {"m": "Masculin", "f": "Féminin", "e": "Epicène"}

# ----------------------------------------------------------------
#                               COLORS
# ----------------------------------------------------------------
COLORS = {
    # General
    "BG" : "#12121C",
    "SURFACE" : "#1E1E2E",
    "SURFACE2" : "#2A2A3E",
    "SURFACE3" : "#14141F",
    "SCROLLBAR" : "#3A3A5C",
    "TEXT_TAG" : "#7A8AB8",
    "TEXT" : "#E8E8F0",
    "TEXT2" : "#A0A0B8",
    "BADGE" : "#3A3A5C",
    "NEUTRAL" : "#8A8A9A",
    "ACCENT" : "#4A9EFF",
    "HOVER" : "#3A8EEF",
    "SUCCESS" : "#3DBE7A",
    "ERROR" : "#FF5F5F",

    # Tabs
    "TAB_FG" : "#1E1E2E",
    "TAB_BTN_FG" : "#1A1A2E",
    "TAB_BTN_SELECT" : "#4A9EFF",
    "TAB_BTN_HOVER" : "#3A8EEF",
    "TAB_BTN_DELETE" : "#4A1A1A",
    "TAB_BTN_DELETE_HOVER" : "#6A2A2A",
    "TAB_TEXT" : "#E8E8F0",
    "TAB_TEXT_DIS" : "#5A5A6A",

    # Dictionary
    "DICT_ENTRY_BORDER" : "#3A3A5C",
    "DICT_COPY_BTN_HOVER" : "#3A3A5C",
    "DICT_ADD_BTN_HOVER" : "#2EAA6A",
    "DICT_SUGGEST_FRAME" : "#2A2A3E",
    "DICT_SUGGEST_FRAME_HOVER" : "#3A3A5C",
    "DICT_SUGGEST_TEXT" : "#4A9EFF",

    # Lexicon
    "LEX_WORD_FRAME" : "#2A2A4A",
    "LEX_WORD_FRAME_CUST" : "#2A1A3A",
    "LEX_WORD_FRAME_CUST_HOVER" : "#3A244F",
    "LEX_WORD_FRAME_HOVER" : "#3A3A5C",
    "LEX_TXT_WORD" : "#4A9EFF",
    "LEX_TXT_WORD_CUST" : "#C8A8FF",
    "LEX_CUST_BTN" : "#5A4E8A",
    "LEX_CUST_BTN_HOVER" : "#6A5E9A",
    "LEX_RESET_BTN_HOVER" : "#3A3A5C",
    "LEX_CUST_ADD_BTN_HOVER" : "#2EAA6A",

    # Quiz
    "CARD_WORD" : "#1A2A4A",
    "CARD_DEF" : "#1A3A2A",
    "CARD_WORD_SIDE" : "#3A5A8A",
    "CARD_DEF_SIDE" : "#3A7A5A",
    "CARD_BADGE" : "#2A5A3A",
    "CARD_BADGE_TXT" : "#80C8A0",

    # Analyzer
    "ANALYZER_BTN_HOVER" : "#3A3A5C",
}

GENDER_COLORS = {
    "m": "#4A9EFF",
    "f": "#FF7EB3",
    "e": "#A78BFA",
}