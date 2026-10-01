# -*- coding: utf-8 -*-
"""Глобальные константы."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

TRAIN_RU = os.path.join(DATA_DIR, 'train_ru')
TRAIN_IT = os.path.join(DATA_DIR, 'train_it')
TEST_DIR = os.path.join(DATA_DIR, 'test')

LANGUAGES = {
    'ru': 'Русский',
    'it': 'Итальянский',
}

# Частотные слова: сколько самых частых слов брать в профиль
TOP_WORDS = 300

# Нейросеть: параметры MLP
MLP_HIDDEN = (100, 50)
MLP_MAX_ITER = 500

# Минимальный размер файла для индексации (в символах)
MIN_TEXT_LEN = 100