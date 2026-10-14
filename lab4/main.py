# -*- coding: utf-8 -*-
"""Точка входа приложения машинного перевода EN → RU."""

import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MachineTranslator EN-RU")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()