# -*- coding: utf-8 -*-
"""Метод частотных слов: строим профиль из топ-N слов каждого языка.

Расстояние между профилями — косинусная мера между
нормализованными векторами частот.
"""

import re
import math
from collections import Counter
from config import TOP_WORDS


def tokenize(text: str) -> list[str]:
    """Разбиение на слова: только буквы, нижний регистр."""
    return re.findall(r'[а-яёa-z]+', text.lower())


class FrequentWordsMethod:
    name = 'Частотных слов'

    def build_profile(self, texts: list[str]) -> dict:
        """Строит профиль языка: словарь {слово: частота} по топ-N."""
        cnt = Counter()
        for t in texts:
            cnt.update(tokenize(t))

        top = cnt.most_common(TOP_WORDS)
        total = sum(c for _, c in top) or 1

        profile = {w: c / total for w, c in top}
        return profile

    def detect(self, text: str, profiles: dict) -> tuple[str, float]:
        """Сравнивает текст с профилями через косинусную меру.

        profiles = {'ru': {word: freq}, 'it': {word: freq}}
        Возвращает (язык, уверенность).
        """
        words = tokenize(text)
        if not words:
            return 'ru', 0.0

        cnt = Counter(words)
        total = sum(cnt.values())

        best_lang, best_sim = None, -1.0
        sims = {}

        for lang, prof in profiles.items():
            if not prof:
                continue
            # косинусная мера между частотным вектором текста и профилем
            dot = 0.0
            for w, c in cnt.items():
                if w in prof:
                    dot += (c / total) * prof[w]

            norm_text = math.sqrt(sum((c / total) ** 2
                                      for c in cnt.values()))
            norm_prof = math.sqrt(sum(v ** 2 for v in prof.values()))
            if norm_text == 0 or norm_prof == 0:
                sim = 0.0
            else:
                sim = dot / (norm_text * norm_prof)

            sims[lang] = sim
            if sim > best_sim:
                best_sim = sim
                best_lang = lang

        return best_lang, best_sim