# -*- coding: utf-8 -*-
"""Sentence extraction — метод извлечения предложений по методичке.

Формулы:
    w(t, D) = 0.5 * (1 + tf(t, D) / tf_max(D)) * log(|DB| / df(t))
    Score(S_i) = Σ_{t ∈ S_i} tf(t, S_i) · w(t, D)
    Posd(S_i) = 1 − BD(S_i) / |D|
    Posp(S_i) = 1 − BP(S_i) / |P|
    Weight(S_i) = Score(S_i) · Posd(S_i) · Posp(S_i)
"""

from collections import Counter

from text_utils import (
    split_into_paragraphs,
    split_into_sentences,
    tokenize_words,
    filter_words,
)
from config import MAX_KEYWORDS


class ExtractionMethod:
    name = "Sentence extraction"
    key = "extraction"

    # ------------------------------------------------------------------
    def summarize(self, text: str, corpus, doc_idx: int,
                  language: str = "ru", summary_size: int = 10) -> dict:
        """Строит реферат одного документа с использованием статистик корпуса."""
        paragraphs = split_into_paragraphs(text)
        if not paragraphs:
            return self._empty()

        # --- Разбиение на предложения с позициями ---
        sentences = []          # [{"text","para_idx","pos_in_para","pos_in_doc"}]
        para_lengths = []
        char_offset = 0

        for p_idx, para in enumerate(paragraphs):
            para_lengths.append(len(para))
            cursor = 0
            for s in split_into_sentences(para):
                pos_in_para = para.find(s, cursor)
                if pos_in_para == -1:
                    pos_in_para = cursor
                sentences.append({
                    "text": s,
                    "para_idx": p_idx,
                    "pos_in_para": pos_in_para,
                    "pos_in_doc": char_offset + pos_in_para,
                })
                cursor = pos_in_para + len(s)
            char_offset += len(para) + 2  # +2 = разделитель абзацев "\n\n"

        if not sentences:
            return self._empty()

        doc_len = max(char_offset, 1)
        N_sent = len(sentences)

        # --- tf(t, S_i) для каждого предложения ---
        sent_tf = []
        for s in sentences:
            words = filter_words(tokenize_words(s["text"]), language)
            sent_tf.append(Counter(words))

        # --- Weight(S_i) ---
        weights = []
        for i, s in enumerate(sentences):
            score = sum(
                sent_tf[i][t] * corpus.weight_of_term(t, doc_idx, language)
                for t in sent_tf[i]
            )
            posd = 1 - s["pos_in_doc"] / doc_len
            para_len = para_lengths[s["para_idx"]]
            posp = 1 - s["pos_in_para"] / para_len if para_len else 0.0
            weights.append(score * posd * posp)

        # --- Top-N предложений в исходном порядке ---
        ranked = sorted(range(N_sent), key=lambda i: weights[i], reverse=True)
        top_idx = sorted(ranked[:summary_size])
        summary = [sentences[i]["text"] for i in top_idx]

        # --- Ключевые слова ---
        kw = Counter()
        for i, s in enumerate(sentences):
            for t in sent_tf[i]:
                kw[t] += sent_tf[i][t] * corpus.weight_of_term(t, doc_idx, language)
        keywords = kw.most_common(MAX_KEYWORDS)

        return {
            "summary": summary,
            "keywords": keywords,
            "method": self.key,
            "language": language,
            "sentences_total": N_sent,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _empty() -> dict:
        return {"summary": [], "keywords": [],
                "method": "extraction", "sentences_total": 0}