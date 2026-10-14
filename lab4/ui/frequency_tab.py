# -*- coding: utf-8 -*-
"""Вкладка «Частотный список»."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLineEdit, QLabel, QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt

from core.translator import Translator


class FrequencyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_rows = []
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Поиск по лемме или переводу:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._apply_filter)
        top.addWidget(self.search_edit, 1)

        b_refresh = QPushButton("Обновить")
        b_refresh.clicked.connect(lambda: self._fill(self.all_rows))
        top.addWidget(b_refresh)

        lay.addLayout(top)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Английская лемма", "Перевод",
            "POS-тег", "Часть речи", "Детальный тег", "Частота",
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        lay.addWidget(self.table, 1)

    def update_from_result(self, result: dict):
        if not result:
            return
        self.all_rows = Translator.frequency_list(result["all_tokens"])
        self._fill(self.all_rows)

    def _fill(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["lemma"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["translation"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["pos"]))
            self.table.setItem(i, 3, QTableWidgetItem(r["pos_ru"]))
            self.table.setItem(i, 4, QTableWidgetItem(r["tag"]))
            item = QTableWidgetItem()
            item.setData(Qt.ItemDataRole.DisplayRole, r["count"])
            self.table.setItem(i, 5, item)
        self.table.setSortingEnabled(True)

    def _apply_filter(self):
        q = self.search_edit.text().strip().lower()
        if not q:
            self._fill(self.all_rows)
            return
        filtered = [
            r for r in self.all_rows
            if q in r["lemma"].lower() or q in r["translation"].lower()
        ]
        self._fill(filtered)