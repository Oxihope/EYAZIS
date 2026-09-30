# -*- coding: utf-8 -*-
"""Векторная модель поиска."""

import math
from database import Database
from indexer import Indexer


class SearchResult:
    __slots__ = ('document_id', 'title', 'snippet', 'rank', 'date', 'path')

    def __init__(self, document_id, title, snippet, rank, date, path=''):
        self.document_id = document_id
        self.title = title
        self.snippet = snippet
        self.rank = rank
        self.date = date
        self.path = path


class Search:
    def __init__(self, db: Database, indexer: Indexer):
        self.db = db
        self.indexer = indexer
        self.all_words_together = False
        self.date_start = None
        self.date_end = None
        self.search_query = ""

    def get_query_vector(self, query):
        lemmas = self.indexer.lemmatize(self.indexer.tokenize(query))
        vec = {}
        for lt in set(lemmas):
            lid = self.db.get_lemma_id(lt)
            if lid is not None:
                vec[lid] = 1.0
        return vec

    @staticmethod
    def scalar_product(a, b):
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(k, 0.0) for k, v in a.items())

    @staticmethod
    def euclidean_norm(a):
        return math.sqrt(sum(v * v for v in a.values()))

    def get_search_result(self):
        q = self.get_query_vector(self.search_query)
        return self.get_search_result_with_vector(q)

    def get_search_result_with_vector(self, q, ignore_and=False):
        if not q:
            return []
        qn = self.euclidean_norm(q)
        if qn == 0:
            return []

        results = []
        for doc in self.db.get_all_documents():
            d_date = doc['date'] or ''

            if self.date_start and d_date < self.date_start:
                continue
            if self.date_end and d_date > self.date_end:
                continue

            d = self.db.get_doc_vector(doc['id'])
            if not d:
                continue

            # AND-фильтр применяем, только если не передан ignore_and
            if self.all_words_together and not ignore_and:
                if not all(k in d for k in q):
                    continue

            dn = self.euclidean_norm(d)
            if dn == 0:
                continue

            rank = self.scalar_product(d, q) / (dn * qn)
            if rank <= 0:
                continue

            text = doc['text']
            clean = ' '.join(text.split())
            snippet = clean[:300] + ('...' if len(clean) > 300 else '')

            path = doc['path'] if 'path' in doc.keys() else ''
            results.append(SearchResult(
                doc['id'], doc['title'], snippet, rank, d_date, path))

        results.sort(key=lambda r: r.rank, reverse=True)
        return results