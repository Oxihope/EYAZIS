# -*- coding: utf-8 -*-
"""Нейросетевой метод: MLPClassifier на символьных 3-граммах.

Признаки — частоты символьных 3-грамм (top-K).
Классификатор — многослойный перцептрон из sklearn.
"""

from collections import Counter
from sklearn.neural_network import MLPClassifier
from sklearn.feature_extraction import DictVectorizer

from config import MLP_HIDDEN, MLP_MAX_ITER


def char_ngrams(text: str, n: int = 3, top_k: int = 500) -> dict:
    """Возвращает {3-грамма: нормализованная частота}."""
    text = text.lower()
    grams = [text[i:i+n] for i in range(len(text) - n + 1)]
    cnt = Counter(grams)
    total = sum(cnt.values()) or 1
    top = cnt.most_common(top_k)
    return {g: c / total for g, c in top}


class NeuralMethod:
    name = 'Нейросетевой'

    def __init__(self):
        self.vectorizer = DictVectorizer(sparse=True)
        self.model = None
        self.languages = []

    def build_profile(self, texts_by_lang: dict) -> dict:
        """Обучает MLP на текстах.

        texts_by_lang = {'ru': [text, ...], 'it': [text, ...]}
        """
        X_dicts = []
        y = []
        self.languages = sorted(texts_by_lang.keys())

        for lang, texts in texts_by_lang.items():
            for t in texts:
                X_dicts.append(char_ngrams(t))
                y.append(lang)

        X = self.vectorizer.fit_transform(X_dicts)
        self.model = MLPClassifier(
            hidden_layer_sizes=MLP_HIDDEN,
            max_iter=MLP_MAX_ITER,
            random_state=42,
        )
        self.model.fit(X, y)
        return {'model': self.model, 'vec': self.vectorizer}

    def detect(self, text: str, profiles: dict) -> tuple[str, float]:
        if self.model is None:
            return 'ru', 0.0
        x = self.vectorizer.transform([char_ngrams(text)])
        proba = self.model.predict_proba(x)[0]
        idx = proba.argmax()
        lang = self.model.classes_[idx]
        return lang, float(proba[idx])