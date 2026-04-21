#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диалоговое окно для настройки параметров синтеза XTTS, модели и голоса
"""
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QGroupBox, QDoubleSpinBox, QSpinBox, QFormLayout, 
    QRadioButton, QComboBox, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt

class ParamsDialog(QDialog):
    """Диалоговое окно для настройки параметров синтеза XTTS"""
    SPEAKERS = [
        'Claribel Dervla', 'Daisy Studious', 'Gracie Wise', 'Tammie Ema',
        'Alison Dietlinde', 'Ana Florence', 'Annmarie Nele', 'Asya Anara',
        'Brenda Stern', 'Gitta Nikolina', 'Henriette Usha', 'Sofia Hellen',
        'Tammy Grit', 'Tanja Adelina', 'Vjollca Johnnie', 'Andrew Chipper',
        'Badr Odhiambo', 'Dionisio Schuyler', 'Royston Min', 'Viktor Eka'
    ]

    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Параметры синтеза XTTS")
        self.setMinimumSize(550, 750)
        self.resize(600, 800)
        self.setModal(True)
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # === 1. Выбор модели и голоса ===
        model_group = QGroupBox("Модель и голос")
        model_layout = QFormLayout(model_group)

        # Тип модели
        self.model_standard_radio = QRadioButton("Стандартная (XTTS-v2)")
        self.model_finetuned_radio = QRadioButton("Дообученная (Finetuned)")
        self.model_standard_radio.setChecked(True)
        self.model_standard_radio.toggled.connect(self.update_model_view)
        model_radio_layout = QHBoxLayout()
        model_radio_layout.addWidget(self.model_standard_radio)
        model_radio_layout.addWidget(self.model_finetuned_radio)
        model_radio_layout.addStretch()
        model_layout.addRow("Тип модели:", model_radio_layout)

        # Выбор голоса
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(self.SPEAKERS)
        self.voice_combo.setEditable(True)
        model_layout.addRow("Голос (спикер):", self.voice_combo)

        # Клонирование (WAV)
        clone_layout = QHBoxLayout()
        self.speaker_wav_edit = QLineEdit()
        self.speaker_wav_edit.setPlaceholderText("Путь к WAV файлу для клонирования...")
        clone_btn = QPushButton("Обзор...")
        clone_btn.clicked.connect(self.browse_speaker_wav)
        clone_layout.addWidget(self.speaker_wav_edit)
        clone_layout.addWidget(clone_btn)
        model_layout.addRow("Клонирование (WAV):", clone_layout)

        # Путь к дообученной модели
        finetuned_layout = QHBoxLayout()
        self.finetuned_path_edit = QLineEdit()
        self.finetuned_path_edit.setPlaceholderText("Папка с config.json, model.pth, vocab.json")
        finetuned_browse_btn = QPushButton("Обзор...")
        finetuned_browse_btn.clicked.connect(self.browse_finetuned_path)
        finetuned_layout.addWidget(self.finetuned_path_edit)
        finetuned_layout.addWidget(finetuned_browse_btn)
        model_layout.addRow("Путь к модели:", finetuned_layout)

        layout.addWidget(model_group)

        # === 2. Общие параметры синтеза ===
        common_group = QGroupBox("Параметры генерации")
        common_layout = QFormLayout(common_group)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.1, 1.5)
        self.temperature_spin.setSingleStep(0.05)
        self.temperature_spin.setDecimals(2)
        common_layout.addRow("Температура:", self.temperature_spin)

        self.repetition_penalty_spin = QDoubleSpinBox()
        self.repetition_penalty_spin.setRange(1.0, 5.0)
        self.repetition_penalty_spin.setSingleStep(0.1)
        self.repetition_penalty_spin.setDecimals(2)
        common_layout.addRow("Штраф за повторы:", self.repetition_penalty_spin)

        self.length_penalty_spin = QDoubleSpinBox()
        self.length_penalty_spin.setRange(0.5, 2.0)
        self.length_penalty_spin.setSingleStep(0.05)
        self.length_penalty_spin.setDecimals(2)
        common_layout.addRow("Штраф за длину:", self.length_penalty_spin)

        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 100)
        common_layout.addRow("Top K:", self.top_k_spin)

        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.01, 1.0)
        self.top_p_spin.setSingleStep(0.01)
        self.top_p_spin.setDecimals(2)
        common_layout.addRow("Top P:", self.top_p_spin)

        self.num_beams_spin = QSpinBox()
        self.num_beams_spin.setRange(1, 20)
        common_layout.addRow("Num Beams:", self.num_beams_spin)

        layout.addWidget(common_group)

        # === 3. Параметры дообученной модели (скрыты по умолчанию) ===
        finetuned_params_group = QGroupBox("Параметры дообученной модели")
        finetuned_params_layout = QFormLayout(finetuned_params_group)

        self.gpt_cond_len_spin = QSpinBox()
        self.gpt_cond_len_spin.setRange(3, 30)
        finetuned_params_layout.addRow("Длина контекста (сек):", self.gpt_cond_len_spin)

        self.sound_norm_check = QCheckBox("Авто-нормализация громкости образца")
        finetuned_params_layout.addRow("Нормализация образца:", self.sound_norm_check)

        self.finetuned_params_group = finetuned_params_group
        layout.addWidget(finetuned_params_group)

        # Примечание
        note_label = QLabel(
            "ℹ️ Параметры сохраняются автоматически.\n"
            "• Стандартная модель: голос выбирается из списка или клонируется через WAV.\n"
            "• Дообученная модель: используется указанный путь и параметры клонирования."
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

    def update_model_view(self):
        """Переключение видимости блоков параметров"""
        is_finetuned = self.model_finetuned_radio.isChecked()
        self.finetuned_path_edit.setEnabled(is_finetuned)
        self.finetuned_params_group.setVisible(is_finetuned)
        self.adjustSize()

    def browse_speaker_wav(self):
        start_dir = self.config.get("work_dir", str(Path.home()))
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите WAV файл", start_dir, "WAV files (*.wav);;All files (*.*)")
        if filename:
            self.speaker_wav_edit.setText(filename)

    def browse_finetuned_path(self):
        start_dir = self.config.get("finetuned_model_path", str(Path.home()))
        dirname = QFileDialog.getExistingDirectory(self, "Выберите папку с моделью", start_dir)
        if dirname:
            self.finetuned_path_edit.setText(dirname)

    def load_values(self):
        """Загрузить текущие значения из конфига"""
        # Модель
        use_finetuned = self.config.get("use_finetuned_model", False)
        if use_finetuned:
            self.model_finetuned_radio.setChecked(True)
        else:
            self.model_standard_radio.setChecked(True)

        self.voice_combo.setCurrentText(self.config.get("speaker", "Claribel Dervla"))
        self.speaker_wav_edit.setText(self.config.get("speaker_wav", ""))
        self.finetuned_path_edit.setText(self.config.get("finetuned_model_path", ""))

        # Общие
        self.temperature_spin.setValue(self.config.get("temperature", 0.85))
        self.repetition_penalty_spin.setValue(self.config.get("repetition_penalty", 2.0))
        self.length_penalty_spin.setValue(self.config.get("length_penalty", 1.0))
        self.top_k_spin.setValue(self.config.get("top_k", 50))
        self.top_p_spin.setValue(self.config.get("top_p", 0.85))
        self.num_beams_spin.setValue(self.config.get("num_beams", 1))
        
        # Специфичные
        self.gpt_cond_len_spin.setValue(self.config.get("gpt_cond_len", 12))
        self.sound_norm_check.setChecked(self.config.get("sound_norm_refs", True))
        
        self.update_model_view()

    def on_ok(self):
        """Сохранение параметров и закрытие"""
        self.config.set("use_finetuned_model", self.model_finetuned_radio.isChecked())
        self.config.set("speaker", self.voice_combo.currentText())
        self.config.set("speaker_wav", self.speaker_wav_edit.text())
        self.config.set("finetuned_model_path", self.finetuned_path_edit.text())
        
        self.config.set("temperature", self.temperature_spin.value())
        self.config.set("repetition_penalty", self.repetition_penalty_spin.value())
        self.config.set("length_penalty", self.length_penalty_spin.value())
        self.config.set("top_k", self.top_k_spin.value())
        self.config.set("top_p", self.top_p_spin.value())
        self.config.set("num_beams", self.num_beams_spin.value())
        self.config.set("gpt_cond_len", self.gpt_cond_len_spin.value())
        self.config.set("sound_norm_refs", self.sound_norm_check.isChecked())
        self.accept()

    def on_reset(self):
        """Сброс значений по умолчанию"""
        self.model_standard_radio.setChecked(True)
        self.voice_combo.setCurrentText("Claribel Dervla")
        self.speaker_wav_edit.clear()
        self.finetuned_path_edit.clear()
        
        self.temperature_spin.setValue(0.85)
        self.repetition_penalty_spin.setValue(2.0)
        self.length_penalty_spin.setValue(1.0)
        self.top_k_spin.setValue(50)
        self.top_p_spin.setValue(0.85)
        self.num_beams_spin.setValue(1)
        self.gpt_cond_len_spin.setValue(12)
        self.sound_norm_check.setChecked(True)
        self.update_model_view()