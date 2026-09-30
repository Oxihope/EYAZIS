# -*- coding: utf-8 -*-
"""Вкладка «База документов»."""

import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView,
)


class DbTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels(
            ["ID", "Заголовок", "Путь", "Размер, б",
             "mtime", "Дата добавления", "Символов"])
        self.tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.tbl)

        b = QPushButton("Обновить")
        b.clicked.connect(self.refresh)
        lay.addWidget(b)

    def refresh(self):
        docs = self.db.get_all_documents()
        self.tbl.setRowCount(len(docs))
        for i, d in enumerate(docs):
            self.tbl.setItem(i, 0, QTableWidgetItem(str(d['id'])))
            self.tbl.setItem(i, 1, QTableWidgetItem(d['title']))

            path = d['path'] if 'path' in d.keys() else ''
            it = QTableWidgetItem(path)
            it.setToolTip(path)
            self.tbl.setItem(i, 2, it)

            size = d['size'] if 'size' in d.keys() else 0
            self.tbl.setItem(i, 3, QTableWidgetItem(str(size or 0)))

            mt = d['mtime'] if 'mtime' in d.keys() else 0
            mt_str = (datetime.datetime.fromtimestamp(mt)
                      .strftime('%Y-%m-%d %H:%M') if mt else '')
            self.tbl.setItem(i, 4, QTableWidgetItem(mt_str))

            self.tbl.setItem(i, 5, QTableWidgetItem(d['date'] or ''))
            self.tbl.setItem(i, 6, QTableWidgetItem(str(len(d['text']))))