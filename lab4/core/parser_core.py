# -*- coding: utf-8 -*-
"""Синтаксический анализ английского текста через spaCy."""

import spacy

from config import SPACY_MODEL, POS_DESCRIPTIONS_RU


class SyntacticParser:
    _nlp = None

    @property
    def nlp(self):
        if self._nlp is None:
            try:
                self._nlp = spacy.load(SPACY_MODEL)
            except OSError:
                raise RuntimeError(
                    f"Модель spaCy '{SPACY_MODEL}' не установлена.\n"
                    f"Запустите: python -m spacy download {SPACY_MODEL}"
                )
        return self._nlp

    def analyze(self, text: str) -> list[dict]:
        """Возвращает список предложений с токенами и деревом."""
        doc = self.nlp(text)
        result = []
        for idx, sent in enumerate(doc.sents):
            tokens = []
            for tok in sent:
                tokens.append({
                    "text": tok.text,
                    "lemma": tok.lemma_.lower(),
                    "pos": tok.pos_,
                    "tag": tok.tag_,
                    "dep": tok.dep_,
                    "head_text": tok.head.text if tok.head != tok else "ROOT",
                    "index": tok.i,
                })
            result.append({
                "sentence_id": idx + 1,
                "text": sent.text.strip(),
                "tokens": tokens,
                "constituency_tree": self._build_tree(sent.root, 0),
            })
        return result

    def _build_tree(self, token, indent: int) -> str:
        prefix = "  " * indent
        label = self._phrase_label(token)
        line = f"{prefix}({label}: {token.text} [{token.tag_}])"
        lines = [line]
        for child in token.children:
            lines.append(self._build_tree(child, indent + 1))
        return "\n".join(lines)

    @staticmethod
    def _phrase_label(token) -> str:
        pos = token.pos_
        if pos in ("VERB", "AUX"):
            return "VP"
        if pos in ("NOUN", "PROPN", "PRON"):
            return "NP"
        if pos == "ADJ":
            return "ADJP"
        if pos == "ADV":
            return "ADVP"
        if pos == "ADP":
            return "PP"
        return "X"

    @staticmethod
    def get_pos_description(pos: str) -> str:
        return POS_DESCRIPTIONS_RU.get(pos, pos)