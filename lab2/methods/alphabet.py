# -*- coding: utf-8 -*-
"""Алфавитный метод: определяем язык по алфавиту символов.

Если в тексте есть кириллица — русский.
Если только латиница — итальянский.
"""

from collections import Counter

CYRILLIC = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
                'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
LATIN = set('abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ')


class AlphabetMethod:
    name = 'Алфавитный'

    def build_profile(self, texts: list[str]) -> dict:
        """Профиль не нужен — метод работает без обучающих данных."""
        return {}

    def detect(self, text: str, profiles: dict) -> tuple[str, float]:
        """Возвращает (язык, уверенность).

        Уверенность = доля символов «победившего» алфавита
        среди всех букв.
        """
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 'ru', 0.0

        cnt = Counter()
        for c in letters:
            if c in CYRILLIC:
                cnt['ru'] += 1
            elif c in LATIN:
                cnt['it'] += 1

        total = sum(cnt.values())
        if total == 0:
            return 'ru', 0.0

        lang = max(cnt, key=cnt.get)
        confidence = cnt[lang] / total
        return lang, confidence