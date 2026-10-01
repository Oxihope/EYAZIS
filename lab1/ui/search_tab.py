# -*- coding: utf-8 -*-
"""Вкладка «Поиск» с чекбоксом PRF."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QCheckBox, QGroupBox, QGridLayout, QSpinBox,
    QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import pyqtSignal

from prf import expand_query
from config import PRF_TOP_K


class SearchTab(QWidget):
    search_completed = pyqtSignal(list)

    def __init__(self, db, indexer, search, parent=None):
        super().__init__(parent)
        self.db = db
        self.indexer = indexer
        self.search = search
        self.last_results = []
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        # ---------- запрос ----------
        qb = QGroupBox("Поисковый запрос")
        g = QGridLayout(qb)

        g.addWidget(QLabel("Запрос:"), 0, 0)
        self.q_edit = QLineEdit()
        g.addWidget(self.q_edit, 0, 1, 1, 4)

        g.addWidget(QLabel("Дата с:"), 1, 0)
        self.d1 = QLineEdit(); self.d1.setPlaceholderText("ГГГГ-ММ-ДД")
        g.addWidget(self.d1, 1, 1)

        g.addWidget(QLabel("по:"), 1, 2)
        self.d2 = QLineEdit(); self.d2.setPlaceholderText("ГГГГ-ММ-ДД")
        g.addWidget(self.d2, 1, 3)

        self.cb_and = QCheckBox("Искать все слова вместе (AND)")
        g.addWidget(self.cb_and, 2, 0, 1, 2)

        self.cb_prf = QCheckBox("Псевдорелевантное расширение (PRF)")
        self.cb_prf.setToolTip(
            "После первого поиска система возьмёт топ-K результатов,\n"
            "добавит их термины в запрос и выполнит поиск заново.")
        g.addWidget(self.cb_prf, 2, 2)

        g.addWidget(QLabel("K:"), 2, 3)
        self.sb_k = QSpinBox()
        self.sb_k.setRange(1, 20)
        self.sb_k.setValue(PRF_TOP_K)
        g.addWidget(self.sb_k, 2, 4)

        b = QPushButton("Найти")
        b.clicked.connect(self._do_search)
        g.addWidget(b, 3, 0, 1, 5)

        lay.addWidget(qb)

        # ---------- таблица результатов ----------
        self.res_tbl = QTableWidget(0, 5)
        self.res_tbl.setHorizontalHeaderLabels(
            ["ID", "Заголовок", "Фрагмент", "Релевантность", "Дата"])
        self.res_tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.res_tbl.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.res_tbl.setWordWrap(False)
        self.res_tbl.verticalHeader().setDefaultSectionSize(26)
        self.res_tbl.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed)
        lay.addWidget(self.res_tbl)

    def _do_search(self):
        self.search.search_query = self.q_edit.text().strip()
        self.search.all_words_together = self.cb_and.isChecked()
        self.search.date_start = self.d1.text().strip() or None
        self.search.date_end = self.d2.text().strip() or None

        if not self.search.search_query:
            QMessageBox.warning(self, "!", "Введите запрос")
            return

        # 1) обычный поиск
        q = self.search.get_query_vector(self.search.search_query)
        if not q:
            self._fill_table([])
            QMessageBox.information(self, "Результат",
                "Ни одна лемма запроса не найдена в словаре")
            return

        results = self.search.get_search_result_with_vector(q)

        # 2) PRF
        if self.cb_prf.isChecked() and results:
            k = self.sb_k.value()
            top_vecs = [self.db.get_doc_vector(r.document_id)
                        for r in results[:k]]
            q_expanded = expand_query(q, top_vecs)

            # Второй проход — с расширенным запросом, AND отключаем
            results = self.search.get_search_result_with_vector(
                q_expanded, ignore_and=True)

            QMessageBox.information(self, "PRF",
                f"Терминов в исходном запросе: {len(q)}\n"
                f"Терминов в расширенном запросе: {len(q_expanded)}\n"
                f"Использовано документов: {min(k, len(top_vecs))}\n"
                f"AND при повторном поиске: отключён")

        self.last_results = results
        self._fill_table(results)
        self.search_completed.emit(results)

    def _fill_table(self, results):
        self.res_tbl.setRowCount(len(results))
        for i, r in enumerate(results):
            self.res_tbl.setItem(i, 0, QTableWidgetItem(str(r.document_id)))
            self.res_tbl.setItem(i, 1, QTableWidgetItem(r.title))
            item = QTableWidgetItem(r.snippet)
            item.setToolTip(r.snippet)
            self.res_tbl.setItem(i, 2, item)
            self.res_tbl.setItem(i, 3, QTableWidgetItem(f"{r.rank:.4f}"))
            self.res_tbl.setItem(i, 4, QTableWidgetItem(r.date or ''))