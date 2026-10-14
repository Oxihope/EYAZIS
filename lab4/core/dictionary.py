# -*- coding: utf-8 -*-
"""Управление двуязычным англо-русским словарём."""

import json
import os

from config import DICT_PATH


class BilingualDictionary:
    """Словарь: английская лемма -> перевод + POS."""

    def __init__(self, path: str = DICT_PATH):
        self.path = path
        self.data = {}
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self.data = {}
            self.save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"[!] Не удалось загрузить словарь: {e}")
            self.data = {}

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def lookup(self, lemma: str):
        return self.data.get(lemma.lower())

    def add(self, lemma: str, translation: str, pos: str = ""):
        self.data[lemma.lower()] = {
            "translation": translation,
            "pos": pos,
        }
        self.save()

    def remove(self, lemma: str) -> bool:
        key = lemma.lower()
        if key in self.data:
            del self.data[key]
            self.save()
            return True
        return False

    def get_all(self):
        return sorted(self.data.items())

    def size(self) -> int:
        return len(self.data)