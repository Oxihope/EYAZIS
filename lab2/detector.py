# -*- coding: utf-8 -*-
"""Оркестратор: строит профили и определяет язык."""

import time
from text_utils import read_all_files
from config import TRAIN_RU, TRAIN_IT, TEST_DIR, LANGUAGES
from methods.alphabet import AlphabetMethod
from methods.frequent_words import FrequentWordsMethod
from methods.neural import NeuralMethod


class Detector:
    def __init__(self):
        self.methods = {
            'alphabet': AlphabetMethod(),
            'frequent': FrequentWordsMethod(),
            'neural': NeuralMethod(),
        }
        self.profiles = {}
        self._trained = False

    # ------------------------------------------------------------------
    def train(self):
        """Строит профили для всех методов."""
        ru_texts = [t for _, t in read_all_files(TRAIN_RU)]
        it_texts = [t for _, t in read_all_files(TRAIN_IT)]

        if not ru_texts or not it_texts:
            raise RuntimeError(
                "Нет обучающих данных. Проверьте папки data/train_ru и data/train_it")

        texts_by_lang = {'ru': ru_texts, 'it': it_texts}

        # алфавитный — без обучения
        self.profiles['alphabet'] = {}

        # частотные слова — отдельный профиль на язык
        self.profiles['frequent'] = {
            lang: self.methods['frequent'].build_profile(texts)
            for lang, texts in texts_by_lang.items()
        }

        # нейросеть — обучаем на всех текстах
        self.profiles['neural'] = self.methods['neural'].build_profile(texts_by_lang)

        self._trained = True

    # ------------------------------------------------------------------
    def detect(self, text: str, method: str) -> tuple[str, float, float]:
        """Возвращает (язык, уверенность, время_в_мс)."""
        if not self._trained:
            raise RuntimeError("Сначала вызовите train()")

        t0 = time.perf_counter()
        lang, conf = self.methods[method].detect(text, self.profiles[method])
        dt = (time.perf_counter() - t0) * 1000
        return lang, conf, dt

    # ------------------------------------------------------------------
    def detect_all(self, text: str) -> dict:
        """Прогон по всем методам."""
        return {m: self.detect(text, m) for m in self.methods}