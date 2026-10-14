# -*- coding: utf-8 -*-
"""Прямой пословный перевод английского текста на русский."""

from collections import Counter

from config import SKIP_POS, SKIP_LEMMAS
from core.dictionary import BilingualDictionary
from core.parser_core import SyntacticParser
from core.text_utils import inflect_ru


class Translator:
    """Прямой пословный перевод EN → RU с использованием словаря."""

    def __init__(self, dictionary: BilingualDictionary = None):
        self.parser = SyntacticParser()
        self.dict = dictionary or BilingualDictionary()

    def translate(self, text: str) -> dict:
        """Основной метод. Возвращает словарь с предложениями,
        всеми токенами и статистикой."""
        analyses = self.parser.analyze(text)
        sentences = []
        all_tokens = []
        total_words = 0
        translated_words = 0

        for sent in analyses:
            tokens_out = []
            words_ru = []

            for tok in sent["tokens"]:
                if tok["pos"] in SKIP_POS:
                    continue

                if tok["lemma"] in SKIP_LEMMAS:
                    continue

                total_words += 1

                entry = self.dict.lookup(tok["lemma"])
                if entry:
                    translation = entry["translation"]
                    translated_form = inflect_ru(translation, tok["pos"])
                    translated_words += 1
                else:
                    translation = None
                    translated_form = f"<{tok['text']}>"

                info = {
                    "text": tok["text"],
                    "lemma": tok["lemma"],
                    "pos": tok["pos"],
                    "pos_ru": SyntacticParser.get_pos_description(tok["pos"]),
                    "tag": tok["tag"],
                    "translation": translation,
                    "translated_form": translated_form,
                }
                tokens_out.append(info)
                all_tokens.append(info)
                words_ru.append(translated_form)

            text_ru = " ".join(words_ru).capitalize()
            if text_ru and not text_ru.endswith((".", "!", "?")):
                text_ru += "."

            sentences.append({
                "text_en": sent["text"],
                "text_ru": text_ru,
                "tokens": tokens_out,
                "constituency_tree": sent["constituency_tree"],
            })

        stats = {
            "total_words": total_words,
            "translated_words": translated_words,
            "untranslated_words": total_words - translated_words,
            "unique_words": len({t["lemma"] for t in all_tokens}),
        }

        return {
            "sentences": sentences,
            "all_tokens": all_tokens,
            "stats": stats,
        }

    @staticmethod
    def frequency_list(all_tokens: list[dict]) -> list[dict]:
        """Строит частотный список слов с переводами и грамматикой."""
        counter = Counter()
        info_by_lemma = {}

        for t in all_tokens:
            key = (t["lemma"], t["pos"])
            counter[key] += 1
            if key not in info_by_lemma:
                info_by_lemma[key] = {
                    "lemma": t["lemma"],
                    "pos": t["pos"],
                    "pos_ru": t["pos_ru"],
                    "tag": t["tag"],
                    "translation": t["translation"] or "—",
                }

        result = []
        for (lemma, pos), cnt in counter.most_common():
            info = info_by_lemma[(lemma, pos)]
            result.append({
                "lemma": lemma,
                "count": cnt,
                "pos": info["pos"],
                "pos_ru": info["pos_ru"],
                "tag": info["tag"],
                "translation": info["translation"],
            })
        return result