# -*- coding: utf-8 -*-
"""Утилиты обработки текста: токенизация, очистка, фильтрация."""

import re
import pymorphy3
from config import (
    RUSSIAN_STOP_WORDS,
    ITALIAN_STOP_WORDS,
    MIN_SENTENCE_LEN,
)

_MORPH = pymorphy3.MorphAnalyzer()

def clean_text(text: str) -> str:
    """Нормализация пробелов с сохранением пустых строк-разделителей."""
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_into_paragraphs(text: str) -> list[str]:
    """Разбиение на абзацы (по пустым строкам)."""
    return [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]


def split_into_sentences(text: str) -> list[str]:
    """Разбиение текста на предложения (по .!?)."""
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if len(p.strip()) >= MIN_SENTENCE_LEN]


def tokenize_words(text: str) -> list[str]:
    """Слова: только буквы, нижний регистр."""
    return re.findall(r'[а-яёa-z]+', text.lower())


def lemmatize_word(word: str, language: str = "ru") -> str:
    """Приводит слово к начальной форме (только для русского)."""
    if language == "ru":
        try:
            return _MORPH.parse(word)[0].normal_form
        except Exception:
            return word
    return word


def filter_words(words: list[str], language: str = "ru") -> list[str]:
    """Фильтрация стоп-слов + лемматизация (для русского)."""
    stop = ITALIAN_STOP_WORDS if language == "it" else RUSSIAN_STOP_WORDS
    result = []
    for w in words:
        if w in stop or len(w) < 3:
            continue
        result.append(lemmatize_word(w, language))
    return result

def detect_language(text: str) -> str:
    """Простейшее определение языка по алфавиту."""
    cyr = sum(1 for c in text if 'а' <= c.lower() <= 'я' or c.lower() == 'ё')
    lat = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    return "ru" if cyr >= lat else "it"