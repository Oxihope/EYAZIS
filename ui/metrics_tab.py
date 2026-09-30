# -*- coding: utf-8 -*-
"""Вкладка «Метрики»."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QDialog, QDialogButtonBox, QCheckBox,
    QHeaderView, QMessageBox,
)

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from metrics import Metrics


class MetricsTab(QWidget):
    def __init__(self, db, get_last_results, parent=None):
        super().__init__(parent)
        self.db = db
        self.get_last_results = get_last_results
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(
            "1) Выполните поиск на вкладке «Поиск».\n"
            "2) Нажмите «Рассчитать метрики» и отметьте релевантные документы.\n"
            "3) Метрики и график появятся ниже."))

        b = QPushButton("Рассчитать метрики")
        b.clicked.connect(self._calc_metrics)
        lay.addWidget(b)

        self.met_tbl = QTableWidget(0, 2)
        self.met_tbl.setHorizontalHeaderLabels(["Метрика", "Значение"])
        self.met_tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.met_tbl)

        self.fig = Figure(figsize=(8, 3.6))
        self.canvas = FigureCanvas(self.fig)
        lay.addWidget(self.canvas)

    def _calc_metrics(self):
        results = self.get_last_results()
        if not results:
            QMessageBox.warning(self, "!", "Сначала выполните поиск")
            return

        all_docs = self.db.get_all_documents()
        retrieved_ids = {r.document_id for r in results}

        # --- диалог экспертной оценки ---
        dlg = QDialog(self)
        dlg.setWindowTitle("Экспертная оценка релевантности")
        dlg.resize(700, 500)
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel("Отметьте документы, релевантные запросу:"))

        tbl = QTableWidget(len(all_docs), 3)
        tbl.setHorizontalHeaderLabels(["ID", "Заголовок", "Релевантен"])
        tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)

        checks = []
        for i, d in enumerate(all_docs):
            tbl.setItem(i, 0, QTableWidgetItem(str(d['id'])))
            tbl.setItem(i, 1, QTableWidgetItem(d['title']))
            cb = QCheckBox()
            if d['id'] in retrieved_ids:
                cb.setStyleSheet("background:#e8f4ff;")
            tbl.setCellWidget(i, 2, cb)
            checks.append(cb)

        v.addWidget(tbl)
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        v.addWidget(bb)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        relevant_ids = {all_docs[i]['id']
                        for i, cb in enumerate(checks) if cb.isChecked()}

        # --- TP/FP/FN/TN ---
        tp = len(retrieved_ids & relevant_ids)
        fp = len(retrieved_ids - relevant_ids)
        fn = len(relevant_ids - retrieved_ids)
        tn = len(all_docs) - len(retrieved_ids | relevant_ids)

        flags = [1 if r.document_id in relevant_ids else 0 for r in results]
        R = len(relevant_ids)

        p = Metrics.precision(tp, fp)
        r = Metrics.recall(tp, fn)

        data = [
            ("Precision",         p),
            ("Recall",            r),
            ("F1",                Metrics.f1(p, r)),
            ("Accuracy",          Metrics.accuracy(tp, tn, fp, fn)),
            ("Error",             Metrics.error(tp, tn, fp, fn)),
            ("Average Precision", Metrics.average_precision(flags)),
            ("Precision@5",       Metrics.precision_at_k(flags, 5)),
            ("Precision@10",      Metrics.precision_at_k(flags, 10)),
            ("R-Precision",       Metrics.r_precision(flags, R)),
        ]

        self.met_tbl.setRowCount(len(data))
        for i, (n, val) in enumerate(data):
            self.met_tbl.setItem(i, 0, QTableWidgetItem(n))
            self.met_tbl.setItem(i, 1, QTableWidgetItem(f"{val:.3f}"))

        # --- диаграмма ---
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        names = [d[0] for d in data]
        vals = [d[1] for d in data]
        bars = ax.bar(names, vals, color='steelblue')
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("Значение")
        ax.set_title("Метрики качества поиска")
        ax.tick_params(axis='x', rotation=30)
        for b, v_ in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v_ + 0.02,
                    f"{v_:.3f}", ha='center', fontsize=9)
        self.fig.tight_layout()
        self.canvas.draw()