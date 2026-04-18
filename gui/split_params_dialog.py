#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диалоговое окно для настройки параметров разбиения текста
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QGroupBox, QSpinBox, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt


class SplitParamsDialog(QDialog):
    """Диалоговое окно для настройки параметров разбиения текста"""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Параметры разбиения текста")
        self.setMinimumSize(500, 550)
        self.resize(550, 600)
        self.setModal(True)
        
        self.setup_ui()
        self.load_values()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Пояснение
        info_label = QLabel(
            "Настройка разбиения текста на фрагменты.\n"
            "Фрагменты оптимальной длины помогают избежать артефактов (хвостов).\n\n"
            "Алгоритм работы:\n"
            "1. Базовое разбиение по главным разделителям\n"
            "2. Объединение коротких фрагментов до минимальной длины\n"
            "3. Разбиение длинных фрагментов по второстепенным разделителям\n"
            "4. Объединение коротких фрагментов (второй проход)\n"
            "5. Восстановление знаков препинания по исходному тексту\n"
            "6. Добавление символа завершения в конец фрагмента\n"
            "7. Нормализация пробелов"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
        
        # Группа параметров длины
        length_group = QGroupBox("Параметры длины")
        length_layout = QFormLayout(length_group)
        
        # Минимальная длина
        self.min_length_spin = QSpinBox()
        self.min_length_spin.setRange(50, 200)
        self.min_length_spin.setSingleStep(10)
        self.min_length_spin.setToolTip("Фрагменты короче этого значения будут объединены с соседними")
        length_layout.addRow("Минимальная длина фрагмента:", self.min_length_spin)
        
        # Максимальная длина
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(150, 500)
        self.max_length_spin.setSingleStep(10)
        self.max_length_spin.setToolTip("Фрагменты длиннее этого значения будут разбиты по второстепенным разделителям")
        length_layout.addRow("Максимальная длина фрагмента:", self.max_length_spin)
        
        layout.addWidget(length_group)
        
        # Группа разделителей
        delimiter_group = QGroupBox("Разделители")
        delimiter_layout = QFormLayout(delimiter_group)
        
        # Главные разделители
        self.primary_edit = QLineEdit()
        self.primary_edit.setPlaceholderText("Пример: .!?")
        self.primary_edit.setToolTip("Символы, по которым происходит базовое разбиение")
        delimiter_layout.addRow("Главные разделители:", self.primary_edit)
        
        # Второстепенные разделители
        self.secondary_edit = QLineEdit()
        self.secondary_edit.setPlaceholderText("Пример: :;")
        self.secondary_edit.setToolTip("Символы для разбиения длинных фрагментов")
        delimiter_layout.addRow("Второстепенные разделители:", self.secondary_edit)
        
        # Символ завершения
        self.terminator_edit = QLineEdit()
        self.terminator_edit.setPlaceholderText(". ! ? ... или пробел")
        self.terminator_edit.setToolTip("Символ, добавляемый в конец фрагмента")
        delimiter_layout.addRow("Символ завершения:", self.terminator_edit)
        
        layout.addWidget(delimiter_group)
        
        # Примечание
        note_label = QLabel(
            "Примечание:\n"
            "• В конце фрагмента запятая (,) заменяется на точку (.)\n"
            "• В начале фрагмента удаляются недопустимые знаки (.,;:...)\n"
            "• Первая буква фрагмента делается заглавной\n"
            "• Кавычки и скобки сохраняются из исходного текста"
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(note_label)
        
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
        self.min_length_spin.setValue(self.config.get("split_min_length", 150))
        self.max_length_spin.setValue(self.config.get("split_max_length", 250))
        self.primary_edit.setText(self.config.get("split_primary_delimiters", ".!?"))
        self.secondary_edit.setText(self.config.get("split_secondary_delimiters", ":;"))
        self.terminator_edit.setText(self.config.get("split_terminator", "."))
    
    def on_ok(self):
        """Сохранение параметров и закрытие"""
        self.config.set("split_min_length", self.min_length_spin.value())
        self.config.set("split_max_length", self.max_length_spin.value())
        self.config.set("split_primary_delimiters", self.primary_edit.text())
        self.config.set("split_secondary_delimiters", self.secondary_edit.text())
        self.config.set("split_terminator", self.terminator_edit.text())
        self.accept()
    
    def on_reset(self):
        """Сброс значений по умолчанию"""
        self.min_length_spin.setValue(150)
        self.max_length_spin.setValue(250)
        self.primary_edit.setText(".!?")
        self.secondary_edit.setText(":;")
        self.terminator_edit.setText(".")