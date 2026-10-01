# -*- coding: utf-8 -*-
"""Извлечение чистого текста из HTML-файлов."""

import os
import re
from bs4 import BeautifulSoup


def extract_text_from_html(path: str) -> str:
    """Читает HTML, удаляет теги script/style, возвращает чистый текст."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # удаляем скрипты и стили — там нет полезного текста
    for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
        tag.decompose()

    text = soup.get_text(separator=' ')

    # сжимаем пробелы и переносы
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def read_all_files(folder: str) -> list[tuple[str, str]]:
    """Возвращает список (путь, текст) для всех .html и .htm в папке."""
    result = []
    if not os.path.isdir(folder):
        return result
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith(('.html', '.htm')):
            full = os.path.join(folder, name)
            try:
                text = extract_text_from_html(full)
                if len(text) >= 100:
                    result.append((full, text))
            except Exception as e:
                print(f"[!] Ошибка чтения {full}: {e}")
    return result