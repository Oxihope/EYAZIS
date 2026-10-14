# -*- coding: utf-8 -*-
"""Конфигурация приложения машинного перевода EN -> RU."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DICT_PATH = os.path.join(DATA_DIR, "en_ru_dict.json")

SOURCE_LANG = "en"
TARGET_LANG = "ru"
SPACY_MODEL = "en_core_web_sm"

# Расшифровка POS-тегов (Universal POS tags из spaCy)
POS_DESCRIPTIONS_RU = {
    "ADJ":   "прилагательное",
    "ADP":   "предлог",
    "ADV":   "наречие",
    "AUX":   "вспомогательный глагол",
    "CCONJ": "сочинительный союз",
    "DET":   "определитель",
    "INTJ":  "междометие",
    "NOUN":  "существительное",
    "NUM":   "числительное",
    "PART":  "частица",
    "PRON":  "местоимение",
    "PROPN": "имя собственное",
    "PUNCT": "знак препинания",
    "SCONJ": "подчинительный союз",
    "SYM":   "символ",
    "VERB":  "глагол",
    "X":     "прочее",
    "SPACE": "пробел",
}

# POS-теги, которые полностью игнорируются при переводе
SKIP_POS = {"PUNCT", "SPACE", "SYM", "X"}

# Артикли и служебные определители — не переводятся
SKIP_LEMMAS = {"the", "a", "an"}