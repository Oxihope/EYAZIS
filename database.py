# -*- coding: utf-8 -*-
"""Слой хранения данных (SQLite)."""

import sqlite3
import datetime
from config import DB_PATH


class Database:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS documents (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                path  TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                text  TEXT NOT NULL,
                date  TEXT,
                time  TEXT,
                mtime REAL,
                size  INTEGER
            );
            CREATE TABLE IF NOT EXISTS lemmas (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                lemma TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS doc_lemma (
                doc_id   INTEGER,
                lemma_id INTEGER,
                qty      INTEGER,
                weight   REAL,
                PRIMARY KEY (doc_id, lemma_id),
                FOREIGN KEY (doc_id)   REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (lemma_id) REFERENCES lemmas(id)    ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS inverse_freq (
                lemma_id INTEGER PRIMARY KEY,
                b REAL,
                FOREIGN KEY (lemma_id) REFERENCES lemmas(id) ON DELETE CASCADE
            );
        ''')
        self.conn.commit()

    # ---------- документы ----------
    def add_or_update_document(self, path, title, text, mtime, size):
        now = datetime.datetime.now()
        existing = self.conn.execute(
            "SELECT id FROM documents WHERE path=?", (path,)).fetchone()

        if existing:
            doc_id = existing['id']
            self.conn.execute("""
                UPDATE documents
                SET title=?, text=?, mtime=?, size=?,
                    date=?, time=?
                WHERE id=?
            """, (title, text, mtime, size,
                  now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'),
                  doc_id))
            self.conn.execute("DELETE FROM doc_lemma WHERE doc_id=?", (doc_id,))
            self.conn.commit()
            return doc_id

        cur = self.conn.execute("""
            INSERT INTO documents (path, title, text, date, time, mtime, size)
            VALUES (?,?,?,?,?,?,?)
        """, (path, title, text,
              now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'),
              mtime, size))
        self.conn.commit()
        return cur.lastrowid

    def delete_document_by_path(self, path):
        cur = self.conn.execute("DELETE FROM documents WHERE path=?", (path,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_all_documents(self):
        return self.conn.execute(
            "SELECT * FROM documents ORDER BY id").fetchall()

    def count_documents(self):
        return self.conn.execute(
            "SELECT COUNT(*) c FROM documents").fetchone()['c']

    # ---------- леммы ----------
    def get_or_create_lemma(self, lemma_text):
        row = self.conn.execute(
            "SELECT id FROM lemmas WHERE lemma=?", (lemma_text,)).fetchone()
        if row:
            return row['id']
        cur = self.conn.execute(
            "INSERT INTO lemmas (lemma) VALUES (?)", (lemma_text,))
        self.conn.commit()
        return cur.lastrowid

    def get_lemma_id(self, lemma_text):
        row = self.conn.execute(
            "SELECT id FROM lemmas WHERE lemma=?", (lemma_text,)).fetchone()
        return row['id'] if row else None

    # ---------- связи ----------
    def set_doc_lemma(self, doc_id, lemma_id, qty, weight):
        self.conn.execute(
            "INSERT OR REPLACE INTO doc_lemma "
            "(doc_id, lemma_id, qty, weight) VALUES (?,?,?,?)",
            (doc_id, lemma_id, qty, weight))
        self.conn.commit()

    def get_doc_vector(self, doc_id):
        rows = self.conn.execute(
            "SELECT lemma_id, weight FROM doc_lemma WHERE doc_id=?",
            (doc_id,)).fetchall()
        return {r['lemma_id']: r['weight'] for r in rows}

    def count_docs_with_lemma(self, lemma_id):
        return self.conn.execute(
            "SELECT COUNT(DISTINCT doc_id) c FROM doc_lemma WHERE lemma_id=?",
            (lemma_id,)).fetchone()['c']

    # ---------- инверсная частота ----------
    def set_inverse_freq(self, lemma_id, b):
        self.conn.execute(
            "INSERT OR REPLACE INTO inverse_freq (lemma_id, b) VALUES (?,?)",
            (lemma_id, b))
        self.conn.commit()

    # ---------- полная очистка ----------
    def clear(self):
        self.conn.executescript('''
            DELETE FROM doc_lemma; DELETE FROM inverse_freq;
            DELETE FROM lemmas;    DELETE FROM documents;
        ''')
        self.conn.commit()