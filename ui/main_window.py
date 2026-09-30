# -*- coding: utf-8 -*-
"""Главное окно: связка паука, БД, поиска и вкладок."""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox,
    QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox,
)
from PyQt6.QtGui import QAction

from config import DB_PATH
from database import Database
from indexer import Indexer
from search import Search
from watcher import FolderWatcher

from ui.search_tab import SearchTab
from ui.metrics_tab import MetricsTab
from ui.db_tab import DbTab
from ui.watcher_tab import WatcherTab


HELP_HTML = """
<h1>Руководство пользователя</h1>
<p>ИПС на основе векторной модели с автоматическим слежением
за папкой и псевдорелевантным расширением запроса (PRF).</p>

<h2>1. Вкладка «Наблюдение»</h2>
<ol>
  <li>Выберите корневую папку кнопкой «Обзор…».</li>
  <li>Нажмите «Запустить наблюдение». Приложение:
    <ul>
      <li>просканирует папку и все вложенные;</li>
      <li>проиндексирует все найденные .txt и .docx;</li>
      <li>будет каждые 2 секунды проверять изменения.</li>
    </ul>
  </li>
  <li>Паук сравнивает метаданные файлов (mtime и size). При добавлении,
      изменении или удалении файла содержимое перечитывается, БД
      и веса TF-IDF обновляются автоматически.</li>
</ol>

<h2>2. Вкладка «Поиск»</h2>
<ol>
  <li>Введите запрос на русском языке.</li>
  <li>При необходимости ограничьте даты или включите режим AND.</li>
  <li>Установите галочку <b>«Псевдорелевантное расширение (PRF)»</b>.</li>
  <li>Нажмите «Найти».</li>
</ol>

<h2>3. Вкладка «Метрики»</h2>
<p>Рассчитывает 9 метрик качества: Precision, Recall, F1, Accuracy,
Error, AP, P@5, P@10, R-Precision.</p>

<h2>4. Элемент ИИ</h2>
<p>Псевдорелевантное расширение запроса (PRF):
<i>Q_new = Q + beta · mean(top-K)</i>.</p>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Руководство пользователя")
        self.resize(820, 650)
        lay = QVBoxLayout(self)
        br = QTextBrowser()
        br.setHtml(HELP_HTML)
        lay.addWidget(br)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject)
        bb.accepted.connect(self.accept)
        lay.addWidget(bb)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ИПС: векторная модель + паук + PRF (вариант 27)")
        self.resize(1300, 880)

        # --- модель ---
        self.db = Database(DB_PATH)
        self.indexer = Indexer(self.db)
        self.search = Search(self.db, self.indexer)
        self.watcher = FolderWatcher(self)
        self.last_results = []

        # --- связи паука ---
        self.watcher.files_added.connect(self._on_files_added)
        self.watcher.files_modified.connect(self._on_files_modified)
        self.watcher.files_deleted.connect(self._on_files_deleted)
        self.watcher.scan_completed.connect(self._on_scan_completed)

        # --- UI ---
        self._build_menu()
        self._build_tabs()

    def _build_menu(self):
        m = self.menuBar().addMenu("Справка")
        a1 = QAction("Руководство пользователя", self)
        a1.setShortcut("F1")
        a1.triggered.connect(lambda: HelpDialog(self).exec())
        m.addAction(a1)
        m.addSeparator()
        a2 = QAction("О программе", self)
        a2.triggered.connect(self._about)
        m.addAction(a2)

    def _build_tabs(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.search_tab = SearchTab(self.db, self.indexer, self.search)
        self.watcher_tab = WatcherTab(self.watcher,
                                      self._start_watcher,
                                      self._stop_watcher)
        self.metrics_tab = MetricsTab(self.db, lambda: self.last_results)
        self.db_tab = DbTab(self.db)

        tabs.addTab(self.search_tab, "Поиск")
        tabs.addTab(self.watcher_tab, "Наблюдение")
        tabs.addTab(self.metrics_tab, "Метрики")
        tabs.addTab(self.db_tab, "База документов")

        self.search_tab.search_completed.connect(self._on_search_done)

    def _start_watcher(self, path):
        self.watcher.start(path)

    def _stop_watcher(self):
        self.watcher.stop()

    @staticmethod
    def _read_file(path):
        if path.lower().endswith('.txt'):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        if path.lower().endswith('.docx'):
            from docx import Document as D
            return "\n".join(p.text for p in D(path).paragraphs)
        raise ValueError(f"Формат не поддерживается: {path}")

    def _on_files_added(self, paths):
        changed = False
        for p in paths:
            try:
                text = self._read_file(p)
                st = os.stat(p)
                title = os.path.basename(p)
                doc_id = self.db.add_or_update_document(
                    p, title, text, st.st_mtime, st.st_size)
                self.indexer.index_document(doc_id, text, recalc=False)
                self.watcher_tab.append_log(f"[+] {p}")
                changed = True
            except Exception as e:
                self.watcher_tab.append_log(f"[!] {p}: {e}")

        if changed:
            self.indexer.recalc_weights()
            self.db_tab.refresh()

    def _on_files_modified(self, paths):
        for p in paths:
            self.watcher_tab.append_log(f"[~] {p}")
        self._on_files_added(paths)

    def _on_files_deleted(self, paths):
        changed = False
        for p in paths:
            if self.db.delete_document_by_path(p):
                self.watcher_tab.append_log(f"[-] {p}")
                changed = True
        if changed:
            self.indexer.recalc_weights()
            self.db_tab.refresh()

    def _on_scan_completed(self, count):
        self.watcher_tab.status_lbl.setText(
            f"Наблюдение активно, файлов в папке: {count}")

    def _on_search_done(self, results):
        self.last_results = results

    def _about(self):
        QMessageBox.information(self, "О программе",
            "Лабораторная работа №1.\n"
            "ИПС на основе векторной модели.\n"
            "Элемент ИИ: псевдорелевантное расширение запроса (PRF).\n"
            "Автоматическое слежение за папкой документов (паук).\n"
            "Вариант 27: модуль отбора документов.")