#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вкладка настроек приложения (упрощённая)
"""
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QSlider, QCheckBox, QRadioButton,
    QFileDialog, QFrame, QScrollArea
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

        # === Основные настройки озвучки ===
        tts_group = QGroupBox("Основные настройки")
        tts_layout = QVBoxLayout(tts_group)

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

        layout.addWidget(tts_group)

        # === Кнопки параметров ===
        params_layout = QHBoxLayout()
        synth_btn = QPushButton("⚙ Параметры синтеза, модели и голоса")
        synth_btn.clicked.connect(self.parent.open_synth_params)
        params_layout.addWidget(synth_btn)
        split_btn = QPushButton("✂ Параметры разбиения")
        split_btn.clicked.connect(self.parent.open_split_params)
        params_layout.addWidget(split_btn)
        params_layout.addStretch()
        layout.addLayout(params_layout)

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
        self.speed_slider.setValue(int(self.config.get("speed", 1.0) * 100))
        self.mp3_radio.setChecked(self.config.get("output_format", "mp3") == "mp3")
        self.wav_radio.setChecked(self.config.get("output_format", "mp3") != "mp3")
        self.fragment_pause_slider.setValue(int(self.config.get("fragment_pause", 0.2) * 100))
        self.init_pause_slider.setValue(int(self.config.get("initial_pause", 0.0) * 100))
        self.auto_save_check.setChecked(self.config.get("auto_save", True))

    def save_settings(self):
        self.config.set("work_dir", self.work_dir_edit.text())
        self.config.set("speed", self.speed_slider.value() / 100.0)
        self.config.set("output_format", "mp3" if self.mp3_radio.isChecked() else "wav")
        self.config.set("fragment_pause", self.fragment_pause_slider.value() / 100.0)
        self.config.set("initial_pause", self.init_pause_slider.value() / 100.0)
        self.config.set("auto_save", self.auto_save_check.isChecked())

    def get_settings(self) -> dict:
        """Получить базовые настройки (без модели/голоса)"""
        return {
            "speed": self.speed_slider.value() / 100.0,
            "output_format": "mp3" if self.mp3_radio.isChecked() else "wav",
            "fragment_pause": self.fragment_pause_slider.value() / 100.0,
            "initial_pause": self.init_pause_slider.value() / 100.0,
        }