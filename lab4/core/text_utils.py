# -*- coding: utf-8 -*-
"""Утилиты обработки текста: лемматизация и склонение русского."""

import re
import pymorphy3

_morph = pymorphy3.MorphAnalyzer()


def tokenize_words(text: str) -> list[str]:
    """Простая токенизация: только буквы."""
    return re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', text)


def lemmatize_ru(word: str) -> str:
    """Приведение русского слова к нормальной форме."""
    parsed = _morph.parse(word)
    if not parsed:
        return word
    return parsed[0].normal_form


def inflect_ru(word: str, pos: str = "") -> str:
    """Приведение русского перевода к базовой форме по POS-тегу.

    Для существительного — именительный падеж, ед.ч.
    Для глагола — инфинитив.
    Для прилагательного — м.р., ед.ч., им.п.
    Для остальных — нормальная форма.
    """
    parsed = _morph.parse(word)
    if not parsed:
        return word

    if pos == "NOUN":
        grammemes = {"nomn", "sing"}
    elif pos == "VERB":
        grammemes = {"INFN"}
    elif pos == "ADJ":
        grammemes = {"nomn", "sing", "masc"}
    else:
        return parsed[0].normal_form

    inflected = parsed[0].inflect(grammemes)
    return inflected.word if inflected else parsed[0].normal_form