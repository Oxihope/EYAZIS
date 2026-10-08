# -*- coding: utf-8 -*-
"""Окно справки."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox
)


HELP_HTML = """
<h1>Руководство пользователя</h1>

<p>Приложение автоматического реферирования коллекции текстовых
документов (русский / итальянский). Документы лежат в папке
<code>docs/</code> рядом с <code>main.py</code>.</p>

<h2>1. Основной сценарий</h2>
<ol>
  <li>Положите <code>.txt</code> файлы в папку <code>docs/</code>.</li>
  <li>Нажмите <b>«Обработать коллекцию»</b> (Ctrl+R).</li>
  <li>В таблице появятся все документы с ключевыми словами.</li>
  <li>Кликните строку — справа откроется реферат выбранного документа.</li>
  <li>Двойной клик по имени файла — открыть исходный документ.</li>
</ol>

<h2>2. Методы</h2>

<h3>Sentence extraction (по методичке)</h3>
<p>Для каждого документа вычисляется вес каждого предложения:</p>
<p><i>w(t, D) = 0.5 · (1 + tf(t, D) / tf<sub>max</sub>(D)) · log(|DB| / df(t))</i></p>
<p><i>Score(S<sub>i</sub>) = Σ<sub>t∈S<sub>i</sub></sub> tf(t, S<sub>i</sub>) · w(t, D)</i></p>
<p><i>Posd(S<sub>i</sub>) = 1 − BD(S<sub>i</sub>) / |D|</i></p>
<p><i>Posp(S<sub>i</sub>) = 1 − BP(S<sub>i</sub>) / |P|</i></p>
<p><i>Weight(S<sub>i</sub>) = Score(S<sub>i</sub>) · Posd(S<sub>i</sub>) · Posp(S<sub>i</sub>)</i></p>
<p>Берутся топ-N предложений и возвращаются в порядке появления в тексте.</p>
<p>Здесь |DB| — <b>число документов в коллекции</b>, df(t) — в скольких
документах встречается термин t. Это ключевое отличие от одно-документного
случая: IDF считается по всей папке <code>docs/</code>.</p>

<h3>TextRank (дополнительный)</h3>
<p>Граф предложений, рёбра — косинусное сходство множеств слов.
Итеративно вычисляются ранги, берутся топ-N.</p>

<h2>3. Настройки</h2>
<ul>
  <li><b>Метод</b> — extraction / textrank.</li>
  <li><b>Размер реферата</b> — сколько предложений включать (5–20).</li>
  <li><b>Язык</b> — определяется автоматически по алфавиту каждого документа.</li>
</ul>

<h2>4. Экспорт и печать</h2>
<ul>
  <li><b>Ctrl+S</b> — сохранить таблицу в CSV (UTF-8-BOM, разделитель «;»).</li>
  <li><b>Ctrl+P</b> — печать сводного отчёта.</li>
</ul>

<h2>5. Возможные проблемы</h2>
<ul>
  <li><b>Таблица пуста</b> — проверьте, что в <code>docs/</code> есть
      <code>.txt</code> файлы, и их размер не меньше 200 символов.</li>
  <li><b>Много мусорных слов</b> — стоп-слова в <code>config.py</code>
      можно дополнить под свой корпус.</li>
</ul>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Руководство пользователя")
        self.resize(800, 640)

        lay = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setHtml(HELP_HTML)
        lay.addWidget(browser)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.reject)
        bb.accepted.connect(self.accept)
        lay.addWidget(bb)