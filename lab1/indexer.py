# -*- coding: utf-8 -*-
"""Индексирование: токенизация, лемматизация, TF-IDF."""

import math
from collections import Counter

import pymorphy3
from nltk.tokenize import sent_tokenize, word_tokenize

from config import STOP_WORDS, CATEGORIES
from database import Database


class Indexer:
    def __init__(self, db):
        self.db: Database = db
        self.morph = pymorphy3.MorphAnalyzer()

    def tokenize(self, text):
        text = text.lower()
        tokens = []
        for sent in sent_tokenize(text, language='russian'):
            for w in word_tokenize(sent, language='russian'):
                if w.isalpha() and any(
                        c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for c in w):
                    tokens.append(w)
        return tokens

    def lemmatize(self, tokens):
        out = []
        for t in tokens:
            p = self.morph.parse(t)[0]
            if p.tag.POS in CATEGORIES and t not in STOP_WORDS:
                out.append(p.normal_form)
        return out

    def index_document(self, doc_id, text, recalc=True):
        lemmas = self.lemmatize(self.tokenize(text))
        counter = Counter(lemmas)

        for lemma_text, qty in counter.items():
            lemma_id = self.db.get_or_create_lemma(lemma_text)
            self.db.set_doc_lemma(doc_id, lemma_id, qty, 0.0)

        if recalc:
            self.recalc_weights()

    def recalc_weights(self):
        N = self.db.count_documents()
        if N == 0:
            return

        rows = self.db.conn.execute(
            "SELECT doc_id, lemma_id, qty FROM doc_lemma").fetchall()

        b_cache = {}
        weights = {}
        norms = {}

        for r in rows:
            lid = r['lemma_id']
            if lid not in b_cache:
                P_i = self.db.count_docs_with_lemma(lid)
                b_cache[lid] = math.log(N / P_i) if P_i > 0 else 0.0
                self.db.set_inverse_freq(lid, b_cache[lid])

            w = r['qty'] * b_cache[lid]
            weights[(r['doc_id'], lid)] = w
            norms[r['doc_id']] = norms.get(r['doc_id'], 0.0) + w * w

        for did in norms:
            norms[did] = math.sqrt(norms[did]) or 1.0

        for (did, lid), w in weights.items():
            self.db.conn.execute(
                "UPDATE doc_lemma SET weight=? "
                "WHERE doc_id=? AND lemma_id=?",
                (w / norms[did], did, lid))
        self.db.conn.commit()