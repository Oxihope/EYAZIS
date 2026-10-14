# -*- coding: utf-8 -*-
"""Загрузка файлов разных форматов: TXT, RTF, PDF, HTML, DOC, DOCX."""

import os


class FileLoader:
    SUPPORTED_EXT = {".txt", ".rtf", ".pdf", ".html", ".htm", ".doc", ".docx"}

    @staticmethod
    def load(path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".txt":
            return FileLoader._txt(path)
        if ext == ".docx":
            return FileLoader._docx(path)
        if ext == ".pdf":
            return FileLoader._pdf(path)
        if ext in (".html", ".htm"):
            return FileLoader._html(path)
        if ext == ".rtf":
            return FileLoader._rtf(path)
        if ext == ".doc":
            return FileLoader._doc(path)
        raise ValueError(f"Формат не поддерживается: {ext}")

    @staticmethod
    def _txt(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def _docx(path):
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    @staticmethod
    def _pdf(path):
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise RuntimeError("Установите PyPDF2: pip install PyPDF2")
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            parts.append(text)
        return "\n".join(parts)

    @staticmethod
    def _html(path):
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise RuntimeError("Установите beautifulsoup4")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator=" ")

    @staticmethod
    def _rtf(path):
        try:
            from striprtf.striprtf import rtf_to_text
            with open(path, "r", encoding="latin-1") as f:
                return rtf_to_text(f.read())
        except ImportError:
            import re
            with open(path, "r", errors="ignore") as f:
                content = f.read()
            return re.sub(r"\\[a-z]+\d*\s?|[{}]", "", content)

    @staticmethod
    def _doc(path):
        import subprocess
        try:
            result = subprocess.run(
                ["antiword", path], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
        except FileNotFoundError:
            pass
        raise ValueError("Для .doc установите antiword")

    @staticmethod
    def save(path: str, content: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)