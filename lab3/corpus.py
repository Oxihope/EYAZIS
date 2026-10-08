# -*- coding: utf-8 -*-
"""Загрузка коллекции документов и расчёт статистик по каждому языку."""

import os
import math
from collections import Counter

from config import DOCS_DIR
from text_utils import (
    clean_text,
    tokenize_words,
    filter_words,
    detect_language,
)


class Corpus:
    """Коллекция документов + IDF-статистика отдельно по каждому языку."""

    def __init__(self, folder: str = DOCS_DIR):
        self.folder = folder
        self.documents = []              # [{"name","path","text","language"}, ...]
        self.N = 0                       # общее число документов

        # Статистики хранятся отдельно по языкам
        self.df = {}                     # lang -> Counter(term -> df)
        self.tf = {}                     # lang -> {doc_idx: Counter}
        self.tf_max = {}                 # lang -> {doc_idx: tf_max}
        self.N_lang = {}                 # lang -> число документов языка

    # ------------------------------------------------------------------
    def load(self):
        """Читает все .txt файлы из папки, определяет язык каждого."""
        self.documents = []
        if not os.path.isdir(self.folder):
            return

        for name in sorted(os.listdir(self.folder)):
            if not name.lower().endswith(".txt"):
                continue
            path = os.path.join(self.folder, name)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                text = clean_text(raw)
                if len(text) < 200:
                    continue
                self.documents.append({
                    "name": name,
                    "path": path,
                    "text": text,
                    "language": detect_language(text),
                })
            except Exception as e:
                print(f"[!] Ошибка чтения {path}: {e}")

        self.N = len(self.documents)

    # ------------------------------------------------------------------
    def build_statistics(self, language: str):
        """Считает tf(t,D), df(t) по документам указанного языка.

        Результат сохраняется в self.df[language], self.tf[language],
        self.tf_max[language]. Другие языки не затрагиваются.
        """
        df = Counter()
        tf = {}
        tf_max = {}

        for idx, doc in enumerate(self.documents):
            if doc["language"] != language:
                continue

            words = filter_words(tokenize_words(doc["text"]), language)
            cnt = Counter(words)
            tf[idx] = cnt
            tf_max[idx] = max(cnt.values()) if cnt else 1

            for w in set(words):
                df[w] += 1

        self.df[language] = df
        self.tf[language] = tf
        self.tf_max[language] = tf_max
        self.N_lang[language] = len(tf)

    # ------------------------------------------------------------------
    def weight_of_term(self, term: str, doc_idx: int, language: str) -> float:
        """w(t, D) по методичке — для конкретного языка.

        w(t, D) = 0.5 * (1 + tf(t,D)/tf_max(D)) * log(N_lang / df(t))
        где N_lang — число документов этого языка.
        """
        tf_dict = self.tf.get(language, {})
        tf_max_dict = self.tf_max.get(language, {})
        df_counter = self.df.get(language, Counter())
        N = self.N_lang.get(language, 0)

        tf_d = tf_dict.get(doc_idx, Counter()).get(term, 0)
        tf_m = tf_max_dict.get(doc_idx, 1)
        df_t = df_counter.get(term, 0)

        if tf_d == 0 or df_t == 0 or N == 0:
            return 0.0

        return 0.5 * (1 + tf_d / tf_m) * math.log(N / df_t)