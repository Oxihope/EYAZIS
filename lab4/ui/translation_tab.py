# -*- coding: utf-8 -*-
"""Вкладка «Перевод»."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QPlainTextEdit, QFileDialog, QMessageBox, QGroupBox, QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.file_loader import FileLoader


class TranslationTab(QWidget):
    translation_done = pyqtSignal(dict)

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.result = None
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        # --- панель управления ---
        top = QHBoxLayout()

        b_load = QPushButton("Загрузить файл")
        b_load.clicked.connect(self._load_file)
        top.addWidget(b_load)

        b_translate = QPushButton("Перевести")
        b_translate.clicked.connect(self._translate)
        top.addWidget(b_translate)

        b_clear = QPushButton("Очистить")
        b_clear.clicked.connect(self._clear)
        top.addWidget(b_clear)

        top.addStretch()
        lay.addLayout(top)

        # --- сплиттер: исходник слева, перевод справа ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QGroupBox("Английский текст")
        lh = QVBoxLayout(left)
        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText(
            "Вставьте английский текст или загрузите файл…")
        lh.addWidget(self.input_edit)
        splitter.addWidget(left)

        right = QGroupBox("Русский перевод")
        rh = QVBoxLayout(right)
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText(
            "Здесь появится перевод…")
        rh.addWidget(self.output_edit)
        splitter.addWidget(right)

        splitter.setSizes([600, 600])
        lay.addWidget(splitter, 1)

        # --- статистика ---
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #555;")
        lay.addWidget(self.stats_label)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", "",
            "Все поддерживаемые (*.txt *.docx *.pdf *.html *.htm *.rtf *.doc);;"
            "Текстовые (*.txt);;Word (*.docx *.doc);;PDF (*.pdf);;"
            "HTML (*.html *.htm);;RTF (*.rtf)")
        if not path:
            return
        try:
            text = FileLoader.load(path)
            self.input_edit.setPlainText(text)
            self.stats_label.setText(f"Загружено: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _translate(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "!", "Введите английский текст.")
            return
        try:
            self.result = self.translator.translate(text)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка перевода", str(e))
            return

        parts = []
        for sent in self.result["sentences"]:
            parts.append(sent["text_ru"])
        self.output_edit.setPlainText("\n\n".join(parts))

        s = self.result["stats"]
        self.stats_label.setText(
            f"Всего слов: {s['total_words']} | "
            f"Переведено: {s['translated_words']} | "
            f"Не найдено: {s['untranslated_words']} | "
            f"Уникальных лемм: {s['unique_words']}")

        self.translation_done.emit(self.result)

    def _clear(self):
        self.input_edit.clear()
        self.output_edit.clear()
        self.stats_label.clear()
        self.result = None