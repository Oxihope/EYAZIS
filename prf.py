# -*- coding: utf-8 -*-
"""Псевдорелевантное расширение запроса (PRF)."""

from config import PRF_BETA, PRF_TOP_N_TERMS


def expand_query(query_vec, top_doc_vecs,
                 beta=PRF_BETA, top_n=PRF_TOP_N_TERMS):
    """Q_new = Q + beta * mean(top-K)."""
    new_q = dict(query_vec)

    if top_doc_vecs:
        coef = beta / len(top_doc_vecs)
        for vec in top_doc_vecs:
            for k, v in vec.items():
                new_q[k] = new_q.get(k, 0.0) + coef * v

    positive = {k: v for k, v in new_q.items() if v > 1e-9}

    if top_n and len(positive) > top_n:
        top = sorted(positive.items(), key=lambda x: -x[1])[:top_n]
        return dict(top)

    return positive