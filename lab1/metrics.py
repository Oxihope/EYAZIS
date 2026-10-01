# -*- coding: utf-8 -*-
"""9 метрик качества поиска."""


class Metrics:
    @staticmethod
    def precision(tp, fp):
        return tp / (tp + fp) if (tp + fp) else 0.0

    @staticmethod
    def recall(tp, fn):
        return tp / (tp + fn) if (tp + fn) else 0.0

    @staticmethod
    def f1(p, r):
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @staticmethod
    def accuracy(tp, tn, fp, fn):
        t = tp + tn + fp + fn
        return (tp + tn) / t if t else 0.0

    @staticmethod
    def error(tp, tn, fp, fn):
        return 1.0 - Metrics.accuracy(tp, tn, fp, fn)

    @staticmethod
    def average_precision(flags):
        if not flags or sum(flags) == 0:
            return 0.0
        s, hits = 0.0, 0
        for i, rel in enumerate(flags, 1):
            if rel:
                hits += 1
                s += hits / i
        return s / sum(flags)

    @staticmethod
    def precision_at_k(flags, k):
        top = flags[:k]
        return sum(top) / k if top else 0.0

    @staticmethod
    def r_precision(flags, R):
        if R <= 0:
            return 0.0
        top = flags[:R]
        return sum(top) / R if top else 0.0