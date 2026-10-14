# -*- coding: utf-8 -*-
"""Вкладка «Дерево разбора»."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QPlainTextEdit, QPushButton, QMessageBox,
)
from PyQt6.QtGui import QFont


class TreeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sentences = []
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Предложение:"))
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_change)
        top.addWidget(self.combo, 1)

        b_copy = QPushButton("Скопировать дерево")
        b_copy.clicked.connect(self._copy_tree)
        top.addWidget(b_copy)

        lay.addLayout(top)

        self.tree_edit = QPlainTextEdit()
        self.tree_edit.setReadOnly(True)
        font = QFont("Courier New", 11)
        self.tree_edit.setFont(font)
        lay.addWidget(self.tree_edit, 1)

    def update_from_result(self, result: dict):
        self.sentences = result.get("sentences", []) if result else []
        self.combo.clear()
        for i, sent in enumerate(self.sentences):
            text = sent["text_en"]
            if len(text) > 80:
                text = text[:80] + "…"
            self.combo.addItem(f"[{i+1}] {text}")
        if self.sentences:
            self.combo.setCurrentIndex(0)
            self._on_change(0)
        else:
            self.tree_edit.clear()

    def _on_change(self, idx):
        if idx < 0 or idx >= len(self.sentences):
            self.tree_edit.clear()
            return
        sent = self.sentences[idx]
        text = (f"EN: {sent['text_en']}\n"
                f"RU: {sent['text_ru']}\n\n"
                f"--- Дерево разбора ---\n\n"
                f"{sent['constituency_tree']}")
        self.tree_edit.setPlainText(text)

    def _copy_tree(self):
        if not self.tree_edit.toPlainText():
            return
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.tree_edit.toPlainText())
        QMessageBox.information(self, "OK", "Дерево скопировано в буфер.")