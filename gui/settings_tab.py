#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вкладка настроек
"""

import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QSlider, QCheckBox, QRadioButton,
    QFileDialog, QMessageBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt


class SettingsTab(QWidget):
    """Вкладка настроек приложения"""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        
        # === Рабочая папка ===
        work_dir_group = QGroupBox("Рабочая папка")
        work_dir_layout = QHBoxLayout(work_dir_group)
        
        self.work_dir_edit = QLineEdit()
        self.work_dir_edit.setPlaceholderText("Выберите рабочую папку...")
        work_dir_layout.addWidget(self.work_dir_edit)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_work_dir)
        work_dir_layout.addWidget(browse_btn)
        
        layout.addWidget(work_dir_group)
        
        # === Настройки озвучки ===
        tts_group = QGroupBox("Настройки озвучки")
        tts_layout = QVBoxLayout(tts_group)
        
        # Голос
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Голос:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(self.get_available_speakers())
        self.voice_combo.setEditable(True)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        tts_layout.addLayout(voice_layout)
        
        # Клонирование голоса
        clone_layout = QHBoxLayout()
        clone_layout.addWidget(QLabel("Клонирование (WAV):"))
        self.speaker_wav_edit = QLineEdit()
        self.speaker_wav_edit.setPlaceholderText("Выберите WAV файл...")
        clone_layout.addWidget(self.speaker_wav_edit)
        clone_btn = QPushButton("Обзор...")
        clone_btn.clicked.connect(self.browse_speaker_wav)
        clone_layout.addWidget(clone_btn)
        tts_layout.addLayout(clone_layout)
        
        tts_layout.addWidget(self.create_separator())
        
        # Модель XTTS
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель XTTS:"))
        
        self.use_standard_radio = QRadioButton("Стандартная")
        self.use_standard_radio.setChecked(True)
        self.use_finetuned_radio = QRadioButton("Дообученная")
        
        model_layout.addWidget(self.use_standard_radio)
        model_layout.addWidget(self.use_finetuned_radio)
        model_layout.addStretch()
        tts_layout.addLayout(model_layout)
        
        # Путь к дообученной модели
        finetuned_layout = QHBoxLayout()
        finetuned_layout.addWidget(QLabel("Путь к модели:"))
        self.finetuned_path_edit = QLineEdit()
        self.finetuned_path_edit.setEnabled(False)
        finetuned_layout.addWidget(self.finetuned_path_edit)
        finetuned_browse_btn = QPushButton("Обзор...")
        finetuned_browse_btn.clicked.connect(self.browse_finetuned_model)
        finetuned_layout.addWidget(finetuned_browse_btn)
        tts_layout.addLayout(finetuned_layout)
        
        hint_label = QLabel("config.json, model.pth, vocab.json")
        hint_label.setStyleSheet("color: gray; font-size: 9pt;")
        tts_layout.addWidget(hint_label)
        
        self.use_standard_radio.toggled.connect(
            lambda checked: self.finetuned_path_edit.setEnabled(not checked)
        )
        
        # Скорость речи
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Скорость речи:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.speed_slider)
        self.speed_label = QLabel("1.0x")
        speed_layout.addWidget(self.speed_label)
        tts_layout.addLayout(speed_layout)
        
        # Формат
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Формат:"))
        self.mp3_radio = QRadioButton("MP3")
        self.mp3_radio.setChecked(True)
        self.wav_radio = QRadioButton("WAV")
        format_layout.addWidget(self.mp3_radio)
        format_layout.addWidget(self.wav_radio)
        format_layout.addStretch()
        tts_layout.addLayout(format_layout)
        
        # Паузы
        pause_layout = QHBoxLayout()
        pause_layout.addWidget(QLabel("Пауза между фрагментами:"))
        self.fragment_pause_slider = QSlider(Qt.Horizontal)
        self.fragment_pause_slider.setRange(0, 200)
        self.fragment_pause_slider.setValue(20)
        self.fragment_pause_slider.valueChanged.connect(self.on_fragment_pause_changed)
        pause_layout.addWidget(self.fragment_pause_slider)
        self.fragment_pause_label = QLabel("0.2 сек")
        pause_layout.addWidget(self.fragment_pause_label)
        tts_layout.addLayout(pause_layout)
        
        init_pause_layout = QHBoxLayout()
        init_pause_layout.addWidget(QLabel("Пауза в начале:"))
        self.init_pause_slider = QSlider(Qt.Horizontal)
        self.init_pause_slider.setRange(0, 200)
        self.init_pause_slider.setValue(0)
        self.init_pause_slider.valueChanged.connect(self.on_init_pause_changed)
        init_pause_layout.addWidget(self.init_pause_slider)
        self.init_pause_label = QLabel("0.0 сек")
        init_pause_layout.addWidget(self.init_pause_label)
        tts_layout.addLayout(init_pause_layout)
        
        # Кнопки параметров
        params_layout = QHBoxLayout()
        synth_btn = QPushButton("⚙ Параметры синтеза")
        synth_btn.clicked.connect(self.parent.open_synth_params)
        params_layout.addWidget(synth_btn)
        
        split_btn = QPushButton("✂ Параметры разбиения")
        split_btn.clicked.connect(self.parent.open_split_params)
        params_layout.addWidget(split_btn)
        params_layout.addStretch()
        tts_layout.addLayout(params_layout)
        
        layout.addWidget(tts_group)
        
        # === Словарь исправлений ===
        dict_group = QGroupBox("Словарь исправлений")
        dict_layout = QHBoxLayout(dict_group)
        
        open_dict_btn = QPushButton("📝 Открыть словарь")
        open_dict_btn.clicked.connect(self.parent.open_stress_dict)
        dict_layout.addWidget(open_dict_btn)
        
        create_dict_btn = QPushButton("📄 Создать пример")
        create_dict_btn.clicked.connect(self.parent.create_example_dict)
        dict_layout.addWidget(create_dict_btn)
        
        dict_layout.addStretch()
        layout.addWidget(dict_group)
        
        # === Автосохранение ===
        autosave_layout = QHBoxLayout()
        self.auto_save_check = QCheckBox("Автосохранение настроек")
        self.auto_save_check.setChecked(True)
        autosave_layout.addWidget(self.auto_save_check)
        autosave_layout.addStretch()
        layout.addLayout(autosave_layout)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        parent_layout = QVBoxLayout(self)
        parent_layout.addWidget(scroll)
    
    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line
    
    def get_available_speakers(self):
        return [
            'Claribel Dervla', 'Daisy Studious', 'Gracie Wise', 'Tammie Ema',
            'Alison Dietlinde', 'Ana Florence', 'Annmarie Nele', 'Asya Anara',
            'Brenda Stern', 'Gitta Nikolina', 'Henriette Usha', 'Sofia Hellen',
            'Tammy Grit', 'Tanja Adelina', 'Vjollca Johnnie', 'Andrew Chipper',
            'Badr Odhiambo', 'Dionisio Schuyler', 'Royston Min', 'Viktor Eka'
        ]
    
    def browse_work_dir(self):
        dirname = QFileDialog.getExistingDirectory(
            self, "Выберите рабочую папку",
            self.work_dir_edit.text() or str(Path.home())
        )
        if dirname:
            self.work_dir_edit.setText(dirname)
            self.config.set("work_dir", dirname)
            self.parent.log(f"Рабочая папка: {dirname}")
            self.parent.check_source_folder()
            self.parent.refresh_task_list()
    
    def browse_speaker_wav(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Выберите WAV файл",
            self.work_dir_edit.text() or str(Path.home()),
            "WAV files (*.wav);;All files (*.*)"
        )
        if filename:
            self.speaker_wav_edit.setText(filename)
            self.config.set("speaker_wav", filename)
            self.parent.log(f"Файл для клонирования: {filename}")
    
    def browse_finetuned_model(self):
        dirname = QFileDialog.getExistingDirectory(
            self, "Выберите папку с моделью",
            self.finetuned_path_edit.text() or str(Path.home())
        )
        if dirname:
            needed_files = ['config.json', 'model.pth', 'vocab.json']
            missing = [f for f in needed_files if not os.path.exists(os.path.join(dirname, f))]
            
            if missing:
                self.parent.log(f"Предупреждение: отсутствуют: {', '.join(missing)}")
                reply = QMessageBox.question(
                    self, "Предупреждение",
                    f"Отсутствуют: {', '.join(missing)}\nПродолжить?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            self.finetuned_path_edit.setText(dirname)
            self.parent.log(f"Выбрана папка с моделью: {dirname}")
    
    def on_speed_changed(self, value):
        speed = value / 100.0
        self.speed_label.setText(f"{speed:.1f}x")
    
    def on_fragment_pause_changed(self, value):
        pause = value / 100.0
        self.fragment_pause_label.setText(f"{pause:.1f} сек")
    
    def on_init_pause_changed(self, value):
        pause = value / 100.0
        self.init_pause_label.setText(f"{pause:.1f} сек")
    
    def load_settings(self):
        self.work_dir_edit.setText(self.config.get("work_dir", ""))
        self.voice_combo.setCurrentText(self.config.get("speaker", "Claribel Dervla"))
        self.speed_slider.setValue(int(self.config.get("speed", 1.0) * 100))
        self.mp3_radio.setChecked(self.config.get("output_format", "mp3") == "mp3")
        self.wav_radio.setChecked(self.config.get("output_format", "mp3") != "mp3")
        self.speaker_wav_edit.setText(self.config.get("speaker_wav", ""))
        self.fragment_pause_slider.setValue(int(self.config.get("fragment_pause", 0.2) * 100))
        self.init_pause_slider.setValue(int(self.config.get("initial_pause", 0.0) * 100))
        
        use_finetuned = self.config.get("use_finetuned_model", False)
        if use_finetuned:
            self.use_finetuned_radio.setChecked(True)
        else:
            self.use_standard_radio.setChecked(True)
        self.finetuned_path_edit.setText(self.config.get("finetuned_model_path", ""))
        self.auto_save_check.setChecked(self.config.get("auto_save", True))
    
    def save_settings(self):
        self.config.set("work_dir", self.work_dir_edit.text())
        self.config.set("speaker", self.voice_combo.currentText())
        self.config.set("speed", self.speed_slider.value() / 100.0)
        self.config.set("output_format", "mp3" if self.mp3_radio.isChecked() else "wav")
        self.config.set("speaker_wav", self.speaker_wav_edit.text())
        self.config.set("fragment_pause", self.fragment_pause_slider.value() / 100.0)
        self.config.set("initial_pause", self.init_pause_slider.value() / 100.0)
        self.config.set("use_finetuned_model", self.use_finetuned_radio.isChecked())
        self.config.set("finetuned_model_path", self.finetuned_path_edit.text())
        self.config.set("auto_save", self.auto_save_check.isChecked())
    
    def get_settings(self) -> dict:
        """Получить все настройки для передачи в очередь"""
        return {
            "speaker": self.voice_combo.currentText(),
            "speed": self.speed_slider.value() / 100.0,
            "output_format": "mp3" if self.mp3_radio.isChecked() else "wav",
            "speaker_wav": self.speaker_wav_edit.text(),
            "fragment_pause": self.fragment_pause_slider.value() / 100.0,
            "initial_pause": self.init_pause_slider.value() / 100.0,
            "use_finetuned_model": self.use_finetuned_radio.isChecked(),
            "finetuned_model_path": self.finetuned_path_edit.text()
        }