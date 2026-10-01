# -*- coding: utf-8 -*-
"""Главное окно приложения."""

import os
import csv
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QHeaderView, QAbstractItemView,
    QTabWidget, QTextEdit, QGroupBox, QGridLayout, QMenu,
)
from PyQt6.QtGui import QAction, QColor, QDesktopServices, QFont
from PyQt6.QtCore import Qt, QUrl

from config import TEST_DIR, LANGUAGES
from detector import Detector
from text_utils import read_all_files
from ui.help_dialog import HelpDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Распознавание языка текста (вариант 23)")
        self.resize(1200, 800)

        self.detector = Detector()
        self.test_docs = []
        self.results = []

        self._build_menu()
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_menu(self):
        m = self.menuBar().addMenu("Справка")
        a = QAction("Руководство пользователя", self)
        a.setShortcut("F1")
        a.triggered.connect(lambda: HelpDialog(self).exec())
        m.addAction(a)

    def _build_ui(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # --- вкладка «Определение» ---
        w1 = QWidget()
        lay = QVBoxLayout(w1)

        box = QGroupBox("Управление")
        g = QGridLayout(box)

        self.lbl_status = QLabel("Профили не построены")
        g.addWidget(self.lbl_status, 0, 0, 1, 3)

        b_train = QPushButton("Обучить")
        b_train.clicked.connect(self._train)
        g.addWidget(b_train, 1, 0)

        b_detect = QPushButton("Определить язык")
        b_detect.clicked.connect(self._detect)
        g.addWidget(b_detect, 1, 1)

        b_clear = QPushButton("Очистить")
        b_clear.clicked.connect(self._clear)
        g.addWidget(b_clear, 1, 2)

        lay.addWidget(box)

        # --- таблица результатов ---
        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels([
            "Документ", "Размер, симв.",
            "Алфавитный", "Частотных слов", "Нейросетевой", "Эталон"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setToolTip(
            "Двойной клик по имени файла — открыть документ в браузере.\n"
            "ПКМ — контекстное меню.")
        self.tbl.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl.customContextMenuRequested.connect(self._on_context_menu)

        lay.addWidget(self.tbl)

        # --- кнопки сохранения ---
        h = QHBoxLayout()
        b_save = QPushButton("Сохранить в CSV")
        b_save.clicked.connect(self._save_csv)
        h.addWidget(b_save)

        b_print = QPushButton("Печать")
        b_print.clicked.connect(self._print)
        h.addWidget(b_print)
        h.addStretch()
        lay.addLayout(h)

        tabs.addTab(w1, "Определение")

        # --- вкладка «Сводка» ---
        w2 = QWidget()
        lay2 = QVBoxLayout(w2)
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        lay2.addWidget(self.summary)
        tabs.addTab(w2, "Сводка")

    # ------------------------------------------------------------------
    def _train(self):
        try:
            self.detector.train()
            self.lbl_status.setText("Профили построены ✓")
            QMessageBox.information(self, "OK", "Профили языков построены")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _detect(self):
        try:
            if not self.detector._trained:
                raise RuntimeError("Сначала обучите систему")

            self.test_docs = read_all_files(TEST_DIR)
            if not self.test_docs:
                raise RuntimeError("Нет тестовых документов в data/test/")

            self.results = []
            self.tbl.setRowCount(len(self.test_docs))

            for i, (path, text) in enumerate(self.test_docs):
                name = os.path.basename(path)
                res = self.detector.detect_all(text)
                truth = ('ru' if name.startswith('ru_')
                         else 'it' if name.startswith('it_')
                         else '—')

                row = {'path': path, 'name': name, 'len': len(text),
                       'truth': truth}

                # --- колонка 0: кликабельная ссылка на документ ---
                item_name = QTableWidgetItem(name)
                item_name.setData(Qt.ItemDataRole.UserRole, path)
                item_name.setForeground(QColor("#1565C0"))
                font = QFont()
                font.setUnderline(True)
                item_name.setFont(font)
                item_name.setToolTip(f"Открыть: {path}")
                self.tbl.setItem(i, 0, item_name)

                self.tbl.setItem(i, 1, QTableWidgetItem(str(len(text))))

                for j, method in enumerate(['alphabet', 'frequent', 'neural']):
                    lang, conf, dt = res[method]
                    row[f'{method}_lang'] = lang
                    row[f'{method}_conf'] = conf
                    row[f'{method}_time'] = dt
                    label = LANGUAGES.get(lang, lang)
                    self.tbl.setItem(
                        i, 2 + j,
                        QTableWidgetItem(f"{label} ({conf:.2f})"))

                self.tbl.setItem(i, 5, QTableWidgetItem(
                    LANGUAGES.get(truth, truth)))
                self.results.append(row)

            self._update_summary()
            QMessageBox.information(
                self, "OK",
                f"Обработано документов: {len(self.results)}\n"
                f"Двойной клик по имени файла откроет документ.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    # ------------------------------------------------------------------
    #  Активная ссылка: двойной клик и контекстное меню
    # ------------------------------------------------------------------
    def _on_cell_double_clicked(self, row, col):
        if col != 0:
            return
        item = self.tbl.item(row, 0)
        if not item:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        self._open_path(path)

    def _on_context_menu(self, pos):
        row = self.tbl.rowAt(pos.y())
        if row < 0:
            return
        item = self.tbl.item(row, 0)
        if not item:
            return
        path = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        a_open = menu.addAction("Открыть документ")
        a_open.triggered.connect(lambda: self._open_path(path))

        a_folder = menu.addAction("Показать в папке")
        a_folder.triggered.connect(lambda: self._show_in_folder(path))

        menu.exec(self.tbl.viewport().mapToGlobal(pos))

    @staticmethod
    def _open_path(path):
        if not path or not os.path.exists(path):
            QMessageBox.warning(None, "!", f"Файл не найден:\n{path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))

    @staticmethod
    def _show_in_folder(path):
        if not path:
            return
        folder = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(folder):
            QMessageBox.warning(None, "!", f"Папка не найдена:\n{folder}")
            return
        if os.name == 'nt':
            os.startfile(folder)                        # Windows
        elif os.name == 'posix':
            import subprocess
            subprocess.Popen(['xdg-open', folder])      # Linux

    # ------------------------------------------------------------------
    def _clear(self):
        self.tbl.setRowCount(0)
        self.results = []
        self.summary.clear()

    def _update_summary(self):
        lines = ["Сводная статистика по методам", "=" * 60, ""]
        for method in ['alphabet', 'frequent', 'neural']:
            correct = 0
            total = 0
            times = []
            for r in self.results:
                if r['truth'] in ('ru', 'it'):
                    total += 1
                    if r[f'{method}_lang'] == r['truth']:
                        correct += 1
                times.append(r[f'{method}_time'])

            acc = correct / total if total else 0
            avg_t = sum(times) / len(times) if times else 0
            lines.append(
                f"{method:10s}  "
                f"точность = {acc:.3f}  "
                f"среднее время = {avg_t:6.2f} мс  "
                f"({correct}/{total})")
        lines.append("")
        lines.append(f"Всего документов: {len(self.results)}")
        lines.append("")
        lines.append("Двойной клик по имени файла открывает документ.")
        self.summary.setPlainText("\n".join(lines))

    def _save_csv(self):
        if not self.results:
            QMessageBox.warning(self, "!", "Нет результатов")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить CSV", "results.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(["Документ", "Путь", "Размер", "Эталон",
                        "Алфавитный", "Частотных", "Нейросетевой"])
            for r in self.results:
                w.writerow([
                    r['name'], r['path'], r['len'], r['truth'],
                    LANGUAGES.get(r['alphabet_lang'], ''),
                    LANGUAGES.get(r['frequent_lang'], ''),
                    LANGUAGES.get(r['neural_lang'], ''),
                ])
        QMessageBox.information(self, "OK", f"Сохранено в {path}")

    def _print(self):
        if not self.results:
            QMessageBox.warning(self, "!", "Нет результатов")
            return
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt6.QtGui import QTextDocument

        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        doc = QTextDocument()
        doc.setPlainText(self.summary.toPlainText())
        doc.print(printer)