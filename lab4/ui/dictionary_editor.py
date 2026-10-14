# -*- coding: utf-8 -*-
"""Диалог редактора двуязычного словаря."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView,
    QAbstractItemView, QComboBox,
)
from config import POS_DESCRIPTIONS_RU


class DictionaryEditor(QDialog):
    def __init__(self, dictionary, parent=None):
        super().__init__(parent)
        self.dict = dictionary
        self.setWindowTitle("Редактор двуязычного словаря")
        self.resize(900, 620)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        # --- форма добавления ---
        form = QHBoxLayout()

        form.addWidget(QLabel("Лемма EN:"))
        self.lemma_edit = QLineEdit()
        self.lemma_edit.setPlaceholderText("например, disease")
        form.addWidget(self.lemma_edit, 1)

        form.addWidget(QLabel("Перевод:"))
        self.trans_edit = QLineEdit()
        self.trans_edit.setPlaceholderText("например, заболевание")
        form.addWidget(self.trans_edit, 1)

        form.addWidget(QLabel("POS:"))
        self.pos_combo = QComboBox()
        for key, val in POS_DESCRIPTIONS_RU.items():
            self.pos_combo.addItem(f"{key} — {val}", key)
        form.addWidget(self.pos_combo)

        b_add = QPushButton("Добавить / Обновить")
        b_add.clicked.connect(self._add_or_update)
        form.addWidget(b_add)

        lay.addLayout(form)

        # --- поиск ---
        search = QHBoxLayout()
        search.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._refresh)
        search.addWidget(self.search_edit, 1)
        b_del = QPushButton("Удалить выбранное")
        b_del.clicked.connect(self._delete)
        search.addWidget(b_del)
        lay.addLayout(search)

        # --- таблица ---
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Английская лемма", "Русский перевод", "POS"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

        # --- кнопка закрытия ---
        bottom = QHBoxLayout()
        bottom.addStretch()
        b_close = QPushButton("Закрыть")
        b_close.clicked.connect(self.accept)
        bottom.addWidget(b_close)
        lay.addLayout(bottom)

        self.size_label = QLabel("")
        lay.addWidget(self.size_label)

    def _refresh(self):
        q = self.search_edit.text().strip().lower()
        rows = self.dict.get_all()
        if q:
            rows = [
                (k, v) for k, v in rows
                if q in k.lower() or q in v.get("translation", "").lower()
            ]
        self.table.setRowCount(len(rows))
        for i, (lemma, entry) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(lemma))
            self.table.setItem(i, 1, QTableWidgetItem(
                entry.get("translation", "")))
            self.table.setItem(i, 2, QTableWidgetItem(
                entry.get("pos", "")))
        self.size_label.setText(f"Всего записей в словаре: {self.dict.size()}")

    def _add_or_update(self):
        lemma = self.lemma_edit.text().strip().lower()
        trans = self.trans_edit.text().strip()
        pos = self.pos_combo.currentData()
        if not lemma or not trans:
            QMessageBox.warning(self, "!", "Заполните лемму и перевод.")
            return
        self.dict.add(lemma, trans, pos)
        self.lemma_edit.clear()
        self.trans_edit.clear()
        self._refresh()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "!", "Выберите строку.")
            return
        lemma = self.table.item(row, 0).text()
        if QMessageBox.question(
                self, "?", f"Удалить '{lemma}'?") == QMessageBox.StandardButton.Yes:
            self.dict.remove(lemma)
            self._refresh()