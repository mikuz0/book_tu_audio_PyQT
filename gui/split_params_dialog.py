#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диалоговое окно для настройки параметров разбиения текста
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt


class SplitParamsDialog(QDialog):
    """Диалоговое окно для настройки параметров разбиения текста"""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Параметры разбиения текста")
        self.setMinimumSize(400, 300)
        self.resize(450, 350)
        self.setModal(True)
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Пояснение
        info_label = QLabel(
            "Используется RecursiveCharacterTextSplitter из LangChain.\n"
            "Алгоритм рекурсивно пытается разделить текст по разделителям\n"
            "в порядке приоритета: абзацы → строки → предложения → запятые → пробелы."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)

        # Группа параметров
        group = QGroupBox("Параметры разбиения")
        form_layout = QFormLayout(group)

        # Максимальный размер фрагмента
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(50, 2000)
        self.chunk_size_spin.setSingleStep(10)
        self.chunk_size_spin.setToolTip("Максимальный размер фрагмента в символах")
        form_layout.addRow("Максимальный размер фрагмента:", self.chunk_size_spin)

        # Перекрытие между фрагментами
        self.chunk_overlap_spin = QSpinBox()
        self.chunk_overlap_spin.setRange(0, 500)
        self.chunk_overlap_spin.setSingleStep(10)
        self.chunk_overlap_spin.setToolTip("Перекрытие между соседними фрагментами (для сохранения контекста)")
        form_layout.addRow("Перекрытие (символов):", self.chunk_overlap_spin)

        layout.addWidget(group)

        # Примечание
        note_label = QLabel(
            "Примечание:\n"
            "• Разделители сохраняются в конце фрагментов.\n"
            "• Алгоритм автоматически выбирает оптимальное место разбиения.\n"
            "• Перекрытие помогает сохранить контекст между фрагментами."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(note_label)

        layout.addStretch()

        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        reset_btn = QPushButton("Сбросить")
        reset_btn.clicked.connect(self.on_reset)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(reset_btn)
        layout.addLayout(btn_layout)

    def load_values(self):
        """Загрузить текущие значения из конфига"""
        self.chunk_size_spin.setValue(self.config.get("split_max_length", 250))
        self.chunk_overlap_spin.setValue(self.config.get("split_overlap", 0))

    def on_ok(self):
        """Сохранение параметров и закрытие"""
        self.config.set("split_max_length", self.chunk_size_spin.value())
        self.config.set("split_overlap", self.chunk_overlap_spin.value())
        self.accept()

    def on_reset(self):
        """Сброс значений по умолчанию"""
        self.chunk_size_spin.setValue(250)
        self.chunk_overlap_spin.setValue(0)