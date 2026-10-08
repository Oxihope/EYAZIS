# -*- coding: utf-8 -*-
"""Главное окно приложения реферирования коллекции документов."""

import os
import csv

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog,
    QHeaderView, QAbstractItemView, QGroupBox, QComboBox,
    QSplitter, QFrame, QTextEdit,
)
from PyQt6.QtGui import QAction, QColor, QDesktopServices, QFont
from PyQt6.QtCore import Qt, QUrl

from config import LANGUAGES, DEFAULT_SUMMARY_SIZE, MAX_KEYWORDS, DOCS_DIR
from summarizer import Summarizer
from ui.help_dialog import HelpDialog

METHOD_LABELS = {
    'extraction': 'Извлечение предложений',
    'textrank':   'TextRank (графовый алгоритм)',
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Автоматическое реферирование коллекции документов")
        self.resize(1350, 850)

        self.summarizer = Summarizer()
        self.folder = DOCS_DIR
        self.results = []          # результаты по всем документам
        self.current_row = -1

        self._build_menu()
        self._build_ui()
        self.statusBar().showMessage(f"Папка с документами: {self.folder}")

    # ------------------------------------------------------------------
    def _build_menu(self):
        file_menu = self.menuBar().addMenu("Файл")

        a_choose = QAction("Выбрать папку…", self)
        a_choose.setShortcut("Ctrl+O")
        a_choose.triggered.connect(self._choose_folder)
        file_menu.addAction(a_choose)

        a_run = QAction("Обработать коллекцию", self)
        a_run.setShortcut("Ctrl+R")
        a_run.triggered.connect(self._process_corpus)
        file_menu.addAction(a_run)

        file_menu.addSeparator()

        a_save = QAction("Сохранить отчёт в CSV", self)
        a_save.setShortcut("Ctrl+S")
        a_save.triggered.connect(self._save_csv)
        file_menu.addAction(a_save)

        a_print = QAction("Печать", self)
        a_print.setShortcut("Ctrl+P")
        a_print.triggered.connect(self._print)
        file_menu.addAction(a_print)

        help_menu = self.menuBar().addMenu("Справка")
        a_help = QAction("Руководство пользователя", self)
        a_help.setShortcut("F1")
        a_help.triggered.connect(lambda: HelpDialog(self).exec())
        help_menu.addAction(a_help)

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # --- Компактная панель управления ---
        top = QWidget()
        th = QHBoxLayout(top)
        th.setContentsMargins(0, 0, 0, 0)
        th.setSpacing(8)

        self.lbl_folder = QLabel(f"Папка: {self.folder}")
        self.lbl_folder.setStyleSheet("color: #666;")
        th.addWidget(self.lbl_folder, 1)

        btn_choose = QPushButton("Выбрать папку")
        btn_choose.clicked.connect(self._choose_folder)
        th.addWidget(btn_choose)

        th.addWidget(QLabel("Метод:"))
        self.cb_method = QComboBox()
        for key, label in METHOD_LABELS.items():
            self.cb_method.addItem(label, key)
        th.addWidget(self.cb_method)

        th.addWidget(QLabel("Предложений в реферате:"))
        self.cb_size = QComboBox()
        self.cb_size.addItems(["5", "10", "15", "20"])
        self.cb_size.setCurrentText(str(DEFAULT_SUMMARY_SIZE))
        self.cb_size.setMaximumWidth(70)
        th.addWidget(self.cb_size)

        btn_run = QPushButton("Обработать коллекцию")
        btn_run.clicked.connect(self._process_corpus)
        th.addWidget(btn_run)

        # Ограничиваем высоту панели
        top.setMaximumHeight(44)
        root.addWidget(top)

        # --- Splitter: слева таблица, справа детали ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QGroupBox("Документы коллекции")
        lh = QVBoxLayout(left)
        lh.setContentsMargins(6, 6, 6, 6)

        self.tbl = QTableWidget(0, 2)
        self.tbl.setHorizontalHeaderLabels(["Файл", "Ключевые слова"])
        self.tbl.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.itemSelectionChanged.connect(self._on_row_selected)
        self.tbl.cellDoubleClicked.connect(self._on_cell_double_clicked)
        lh.addWidget(self.tbl)
        splitter.addWidget(left)

        right = QWidget()
        rh = QVBoxLayout(right)
        rh.setContentsMargins(0, 0, 0, 0)

        self.lbl_doc = QLabel("Документ не выбран")
        f = QFont()
        f.setBold(True)
        self.lbl_doc.setFont(f)
        rh.addWidget(self.lbl_doc)

        kw_box = QGroupBox("Ключевые слова (лемматизированные)")
        kw_lay = QVBoxLayout(kw_box)
        kw_lay.setContentsMargins(6, 6, 6, 6)
        self.tbl_kw = QTableWidget(0, 2)
        self.tbl_kw.setHorizontalHeaderLabels(["Слово", "Вес"])
        self.tbl_kw.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.tbl_kw.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        kw_lay.addWidget(self.tbl_kw)
        rh.addWidget(kw_box, 1)

        sum_box = QGroupBox("Классический реферат")
        sum_lay = QVBoxLayout(sum_box)
        sum_lay.setContentsMargins(6, 6, 6, 6)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlaceholderText(
            "Выберите документ в таблице слева…")
        sum_lay.addWidget(self.summary_text)
        rh.addWidget(sum_box, 2)

        splitter.addWidget(right)
        splitter.setSizes([520, 800])
        root.addWidget(splitter, 1)
    
    # ------------------------------------------------------------------
    #  Действия
    # ------------------------------------------------------------------
    def _choose_folder(self):
        d = QFileDialog.getExistingDirectory(
            self, "Выберите папку с документами", self.folder)
        if not d:
            return
        self.folder = d
        self.lbl_folder.setText(f"Папка: <i>{d}</i>")
        self.statusBar().showMessage(f"Выбрана папка: {d}")

    def _process_corpus(self):
        method = self.cb_method.currentData()
        size = int(self.cb_size.currentText())

        try:
            self.results = self.summarizer.process_corpus(
                folder=self.folder, method=method, summary_size=size)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        if not self.results:
            QMessageBox.warning(self, "!", "Нет результатов.")
            return

        self._fill_table()
        self.statusBar().showMessage(
            f"Обработано документов: {len(self.results)}")

    def _fill_table(self):
        self.tbl.setRowCount(len(self.results))
        for i, r in enumerate(self.results):
            item_name = QTableWidgetItem(r["name"])
            item_name.setData(Qt.ItemDataRole.UserRole, r["path"])
            item_name.setForeground(QColor("#1565C0"))
            fnt = QFont()
            fnt.setUnderline(True)
            item_name.setFont(fnt)
            item_name.setToolTip("Двойной клик — открыть документ")
            self.tbl.setItem(i, 0, item_name)

            top_kw = ", ".join(w for w, _ in r["keywords"][:8])
            self.tbl.setItem(i, 1, QTableWidgetItem(top_kw))

        if self.results:
            self.tbl.selectRow(0)
    
    # ------------------------------------------------------------------
    def _on_row_selected(self):
        rows = self.tbl.selectionModel().selectedRows()
        if not rows:
            return
        i = rows[0].row()
        if i < 0 or i >= len(self.results):
            return
        self.current_row = i
        self._show_details(self.results[i])

    def _show_details(self, r: dict):
        self.lbl_doc.setText(
            f"{r['name']}  ({LANGUAGES.get(r['language'], r['language'])}, "
            f"{r['length']} символов, {r.get('sentences_total', 0)} предложений)")

        kw = r["keywords"][:MAX_KEYWORDS]
        self.tbl_kw.setRowCount(len(kw))
        for j, (word, weight) in enumerate(kw):
            self.tbl_kw.setItem(j, 0, QTableWidgetItem(word))
            self.tbl_kw.setItem(j, 1, QTableWidgetItem(f"{weight:.4f}"))

        if r["summary"]:
            self.summary_text.setPlainText(" ".join(r["summary"]))
        else:
            self.summary_text.setPlainText("(реферат пуст)")

    def _on_cell_double_clicked(self, row, col):
        if row < 0 or row >= len(self.results):
            return
        path = self.results[row]["path"]
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))

    # ------------------------------------------------------------------
    #  CSV и печать
    # ------------------------------------------------------------------
    def _save_csv(self):
        if not self.results:
            QMessageBox.warning(self, "!", "Сначала обработайте коллекцию.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт",
            "summarization_report.csv", "CSV (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow([
                    "Файл", "Путь", "Язык", "Символов", "Предложений",
                    "Метод", "Ключевые слова", "Реферат",
                ])
                for r in self.results:
                    w.writerow([
                        r["name"],
                        r["path"],
                        LANGUAGES.get(r["language"], r["language"]),
                        r["length"],
                        r.get("sentences_total", 0),
                        r["method"],
                        ", ".join(w_ for w_, _ in r["keywords"]),
                        " ".join(r["summary"]),
                    ])
            QMessageBox.information(self, "OK", f"Отчёт сохранён в {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _print(self):
        if not self.results:
            QMessageBox.warning(self, "!", "Сначала обработайте коллекцию.")
            return

        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt6.QtGui import QTextDocument

        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        lines = [
            "=" * 72,
            "ОТЧЁТ ПО АВТОМАТИЧЕСКОМУ РЕФЕРИРОВАНИЮ КОЛЛЕКЦИИ",
            "=" * 72,
            f"Папка: {self.folder}",
            f"Метод: {self.results[0]['method'] if self.results else '—'}",
            f"Документов: {len(self.results)}",
            "",
        ]
        for i, r in enumerate(self.results, 1):
            lines.append("-" * 72)
            lines.append(f"[{i}] {r['name']}  ({LANGUAGES.get(r['language'], r['language'])}, "
                         f"{r['length']} символов)")
            lines.append("")
            lines.append("Ключевые слова:")
            for w_, s_ in r["keywords"][:10]:
                lines.append(f"  {w_}  ({s_:.4f})")
            lines.append("")
            lines.append("Реферат:")
            for s in r["summary"]:
                lines.append(f"  • {s}")
            lines.append("")

        doc = QTextDocument()
        doc.setPlainText("\n".join(lines))
        doc.print(printer)