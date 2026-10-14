# -*- coding: utf-8 -*-
"""Главное окно приложения машинного перевода."""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, QFileDialog, QDialog,
)
from PyQt6.QtGui import QAction, QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from core.dictionary import BilingualDictionary
from core.translator import Translator
from ui.translation_tab import TranslationTab
from ui.frequency_tab import FrequencyTab
from ui.tree_tab import TreeTab
from ui.dictionary_editor import DictionaryEditor
from ui.help_dialog import HelpDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Машинный перевод EN → RU (вариант 7)")
        self.resize(1250, 800)

        self.dictionary = BilingualDictionary()
        self.translator = Translator(self.dictionary)
        self.last_result = None

        self._build_menu()
        self._build_tabs()

    def _build_menu(self):
        # Файл
        m_file = self.menuBar().addMenu("Файл")

        a_save = QAction("Сохранить отчёт в TXT", self)
        a_save.setShortcut("Ctrl+S")
        a_save.triggered.connect(self._save_report)
        m_file.addAction(a_save)

        a_print = QAction("Печать", self)
        a_print.setShortcut("Ctrl+P")
        a_print.triggered.connect(self._print)
        m_file.addAction(a_print)

        m_file.addSeparator()
        a_exit = QAction("Выход", self)
        a_exit.setShortcut("Ctrl+Q")
        a_exit.triggered.connect(self.close)
        m_file.addAction(a_exit)

        # Словарь
        m_dict = self.menuBar().addMenu("Словарь")
        a_edit = QAction("Редактор словаря", self)
        a_edit.triggered.connect(self._open_editor)
        m_dict.addAction(a_edit)

        # Справка
        m_help = self.menuBar().addMenu("Справка")
        a_help = QAction("Руководство пользователя", self)
        a_help.setShortcut("F1")
        a_help.triggered.connect(lambda: HelpDialog(self).exec())
        m_help.addAction(a_help)

    def _build_tabs(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.translation_tab = TranslationTab(self.translator)
        self.frequency_tab = FrequencyTab()
        self.tree_tab = TreeTab()

        tabs.addTab(self.translation_tab, "Перевод")
        tabs.addTab(self.frequency_tab, "Частотный список")
        tabs.addTab(self.tree_tab, "Дерево разбора")

        self.translation_tab.translation_done.connect(self._on_translation_done)

    def _on_translation_done(self, result):
        self.last_result = result
        self.frequency_tab.update_from_result(result)
        self.tree_tab.update_from_result(result)

    def _open_editor(self):
        dlg = DictionaryEditor(self.dictionary, self)
        dlg.exec()

    def _save_report(self):
        if not self.last_result:
            QMessageBox.warning(self, "!", "Сначала выполните перевод.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "translation_report.txt",
            "Текстовые файлы (*.txt)")
        if not path:
            return

        lines = []
        lines.append("=" * 72)
        lines.append("ОТЧЁТ ПО МАШИННОМУ ПЕРЕВОДУ EN → RU")
        lines.append("=" * 72)
        lines.append("")

        stats = self.last_result["stats"]
        lines.append(f"Всего слов: {stats['total_words']}")
        lines.append(f"Переведено: {stats['translated_words']}")
        lines.append(f"Не найдено: {stats['untranslated_words']}")
        lines.append(f"Уникальных лемм: {stats['unique_words']}")
        lines.append("")

        lines.append("-" * 72)
        lines.append("ПЕРЕВОД")
        lines.append("-" * 72)
        for sent in self.last_result["sentences"]:
            lines.append(f"EN: {sent['text_en']}")
            lines.append(f"RU: {sent['text_ru']}")
            lines.append("")

        lines.append("-" * 72)
        lines.append("ЧАСТОТНЫЙ СПИСОК")
        lines.append("-" * 72)
        from core.translator import Translator
        freq = Translator.frequency_list(self.last_result["all_tokens"])
        lines.append(f"{'Лемма':<20} {'Перевод':<20} {'POS':<8} {'Частота'}")
        for r in freq:
            lines.append(f"{r['lemma']:<20} {r['translation']:<20} "
                         f"{r['pos']:<8} {r['count']}")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            QMessageBox.information(self, "OK", f"Отчёт сохранён: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _print(self):
        if not self.last_result:
            QMessageBox.warning(self, "!", "Сначала выполните перевод.")
            return

        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        lines = []
        for sent in self.last_result["sentences"]:
            lines.append(f"EN: {sent['text_en']}")
            lines.append(f"RU: {sent['text_ru']}")
            lines.append("")

        doc = QTextDocument()
        doc.setPlainText("\n".join(lines))
        doc.print(printer)