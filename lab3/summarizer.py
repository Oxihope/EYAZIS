# -*- coding: utf-8 -*-
"""Оркестратор: обрабатывает всю коллекцию документов."""

from corpus import Corpus
from methods.extraction import ExtractionMethod
from methods.textrank import TextRankMethod


class Summarizer:
    def __init__(self):
        self.methods = {
            ExtractionMethod.key: ExtractionMethod(),
            TextRankMethod.key: TextRankMethod(),
        }

    # ------------------------------------------------------------------
    def process_corpus(self, folder: str, method: str = "extraction",
                   summary_size: int = 10) -> list[dict]:
        if method not in self.methods:
            raise ValueError(f"Неизвестный метод: {method}")

        corpus = Corpus(folder)
        corpus.load()
        if corpus.N == 0:
            raise RuntimeError(f"В папке {folder} нет .txt файлов.")

        # Статистика считается один раз на язык, сохраняется отдельно
        for lang in ("ru", "it"):
            corpus.build_statistics(lang)

        results = []
        for idx, doc in enumerate(corpus.documents):
            lang = doc["language"]
            r = self.methods[method].summarize(
                text=doc["text"],
                corpus=corpus,
                doc_idx=idx,
                language=lang,
                summary_size=summary_size,
            )
            r["name"] = doc["name"]
            r["path"] = doc["path"]
            r["language"] = lang
            r["length"] = len(doc["text"])
            results.append(r)

        return results
    # ------------------------------------------------------------------
    def method_names(self) -> dict:
        return {k: m.name for k, m in self.methods.items()}