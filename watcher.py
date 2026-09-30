# -*- coding: utf-8 -*-
"""Паук: обходит папку и вложенные, отслеживает изменения."""

import os
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from config import WATCH_INTERVAL_MS, SUPPORTED_EXTS


class FolderWatcher(QObject):
    files_added    = pyqtSignal(list)
    files_modified = pyqtSignal(list)
    files_deleted  = pyqtSignal(list)
    scan_completed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root = None
        self.known = {}                     # path -> (mtime, size)
        self.timer = QTimer(self)
        self.timer.setInterval(WATCH_INTERVAL_MS)
        self.timer.timeout.connect(self._scan)

    def start(self, root):
        self.stop()
        self.root = os.path.abspath(root)
        if not os.path.isdir(self.root):
            raise ValueError(f"Не является папкой: {self.root}")

        self.known = self._scan_tree()
        self.scan_completed.emit(len(self.known))

        if self.known:
            self.files_added.emit(list(self.known.keys()))

        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.root = None
        self.known = {}

    def is_running(self):
        return self.timer.isActive()

    def _scan_tree(self):
        result = {}
        if not self.root:
            return result
        for dirpath, dirnames, filenames in os.walk(self.root):
            for f in filenames:
                if f.lower().endswith(SUPPORTED_EXTS):
                    full = os.path.join(dirpath, f)
                    try:
                        st = os.stat(full)
                        result[full] = (st.st_mtime, st.st_size)
                    except OSError:
                        pass
        return result

    def _scan(self):
        if not self.root:
            return

        current = self._scan_tree()

        added    = [p for p in current if p not in self.known]
        deleted  = [p for p in self.known if p not in current]
        modified = [p for p in current
                    if p in self.known and current[p] != self.known[p]]

        if added:
            self.files_added.emit(added)
        if modified:
            self.files_modified.emit(modified)
        if deleted:
            self.files_deleted.emit(deleted)

        if added or modified or deleted:
            self.scan_completed.emit(len(current))

        self.known = current