# -*- coding: utf-8 -*-
"""Вкладка «Наблюдение за папкой»."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFileDialog, QMessageBox, QGroupBox, QTextEdit
)


class WatcherTab(QWidget):
    def __init__(self, watcher, on_start, on_stop, parent=None):
        super().__init__(parent)
        self.watcher = watcher
        self.on_start = on_start
        self.on_stop = on_stop
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        box = QGroupBox("Папка для отслеживания")
        h = QHBoxLayout(box)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Выберите корневую папку…")
        h.addWidget(self.path_edit, 1)

        b_browse = QPushButton("Обзор…")
        b_browse.clicked.connect(self._browse)
        h.addWidget(b_browse)

        self.b_toggle = QPushButton("Запустить наблюдение")
        self.b_toggle.clicked.connect(self._toggle)
        h.addWidget(self.b_toggle)

        lay.addWidget(box)

        self.status_lbl = QLabel("Наблюдение остановлено")
        lay.addWidget(self.status_lbl)

        lay.addWidget(QLabel("Журнал событий:"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        lay.addWidget(self.log, 1)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if d:
            self.path_edit.setText(d)

    def _toggle(self):
        if self.watcher.is_running():
            self.on_stop()
            self.b_toggle.setText("Запустить наблюдение")
            self.status_lbl.setText("Наблюдение остановлено")
        else:
            path = self.path_edit.text().strip()
            if not path:
                QMessageBox.warning(self, "!", "Выберите папку")
                return
            try:
                self.on_start(path)
                self.b_toggle.setText("Остановить наблюдение")
                self.status_lbl.setText(
                    f"Наблюдение активно: {os.path.abspath(path)}")
                self.append_log(f"Запущено наблюдение за {path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def append_log(self, text):
        self.log.append(text)