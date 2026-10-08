# -*- coding: utf-8 -*-
"""TextRank — графовый алгоритм реферирования (дополнительный метод)."""

from collections import Counter

from text_utils import (
    split_into_sentences,
    tokenize_words,
    filter_words,
)
from config import MAX_KEYWORDS


class TextRankMethod:
    name = "TextRank"
    key = "textrank"

    DAMPING = 0.85
    ITERATIONS = 30
    TOLERANCE = 1e-6

    # ------------------------------------------------------------------
    def summarize(self, text: str, corpus=None, doc_idx=None,
                  language: str = "ru", summary_size: int = 10) -> dict:
        sentences = split_into_sentences(text)
        n = len(sentences)
        if n == 0:
            return self._empty()

        sent_words = [
            set(filter_words(tokenize_words(s), language))
            for s in sentences
        ]

        # --- Матрица сходства (косинусная мера на множествах слов) ---
        sim = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                si, sj = sent_words[i], sent_words[j]
                if not si or not sj:
                    continue
                union = len(si | sj)
                if union:
                    sim[i][j] = sim[j][i] = len(si & sj) / union

        # --- PageRank-подобные итерации ---
        ranks = [1.0 / n] * n
        for _ in range(self.ITERATIONS):
            new_ranks = [(1 - self.DAMPING) / n] * n
            for i in range(n):
                for j in range(n):
                    if i != j and sim[j][i] > 0:
                        row_sum = sum(sim[j])
                        if row_sum > 0:
                            new_ranks[i] += (self.DAMPING
                                             * sim[j][i] / row_sum
                                             * ranks[j])
            diff = sum(abs(new_ranks[i] - ranks[i]) for i in range(n))
            ranks = new_ranks
            if diff < self.TOLERANCE:
                break

        # --- Top-N в исходном порядке ---
        ranked = sorted(range(n), key=lambda i: ranks[i], reverse=True)
        top_idx = sorted(ranked[:summary_size])
        summary = [sentences[i] for i in top_idx]

        # --- Ключевые слова: взвешенная частота ---
        kw = Counter()
        for i, words in enumerate(sent_words):
            for w in words:
                kw[w] += ranks[i]
        keywords = kw.most_common(MAX_KEYWORDS)

        return {
            "summary": summary,
            "keywords": keywords,
            "method": self.key,
            "language": language,
            "sentences_total": n,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _empty() -> dict:
        return {"summary": [], "keywords": [],
                "method": "textrank", "sentences_total": 0}