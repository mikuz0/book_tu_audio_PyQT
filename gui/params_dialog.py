#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диалоговое окно для настройки параметров синтеза XTTS
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QCheckBox, QGroupBox, QDoubleSpinBox,
    QSpinBox, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt


class ParamsDialog(QDialog):
    """Диалоговое окно для настройки параметров синтеза XTTS"""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Параметры синтеза XTTS")
        self.setMinimumSize(500, 600)
        self.resize(550, 650)
        self.setModal(True)
        
        self.setup_ui()
        self.load_values()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Пояснение
        info_label = QLabel(
            "Настройка параметров синтеза речи.\n"
            "Увеличение repetition_penalty помогает бороться с хвостами и повторами.\n"
            "num_beams - количество лучей поиска (1 = быстро, больше = качественнее, но медленнее)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
        
        # Группа параметров
        params_group = QGroupBox("Параметры синтеза")
        form_layout = QFormLayout(params_group)
        
        # Температура
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.1, 1.5)
        self.temperature_spin.setSingleStep(0.05)
        self.temperature_spin.setDecimals(2)
        self.temperature_spin.setToolTip("Чем выше, тем креативнее, но больше артефактов")
        form_layout.addRow("Температура (temperature):", self.temperature_spin)
        
        # Штраф за повторы
        self.repetition_penalty_spin = QDoubleSpinBox()
        self.repetition_penalty_spin.setRange(1.0, 5.0)
        self.repetition_penalty_spin.setSingleStep(0.1)
        self.repetition_penalty_spin.setDecimals(2)
        self.repetition_penalty_spin.setToolTip("Увеличивайте для борьбы с повторами и хвостами")
        form_layout.addRow("Штраф за повторы (repetition_penalty):", self.repetition_penalty_spin)
        
        # Штраф за длину
        self.length_penalty_spin = QDoubleSpinBox()
        self.length_penalty_spin.setRange(0.5, 2.0)
        self.length_penalty_spin.setSingleStep(0.05)
        self.length_penalty_spin.setDecimals(2)
        self.length_penalty_spin.setToolTip("Положительные значения укорачивают фразы")
        form_layout.addRow("Штраф за длину (length_penalty):", self.length_penalty_spin)
        
        # Top K
        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 100)
        self.top_k_spin.setToolTip("Меньше = предсказуемее")
        form_layout.addRow("Top K:", self.top_k_spin)
        
        # Top P
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.01, 1.0)
        self.top_p_spin.setSingleStep(0.01)
        self.top_p_spin.setDecimals(2)
        self.top_p_spin.setToolTip("Меньше = предсказуемее")
        form_layout.addRow("Top P:", self.top_p_spin)
        
        # Num Beams
        self.num_beams_spin = QSpinBox()
        self.num_beams_spin.setRange(1, 20)
        self.num_beams_spin.setToolTip("Количество путей поиска. 1 = быстро, больше = качественнее, но медленнее")
        form_layout.addRow("Num Beams (количество лучей):", self.num_beams_spin)
        
        # GPT cond len
        self.gpt_cond_len_spin = QSpinBox()
        self.gpt_cond_len_spin.setRange(3, 30)
        self.gpt_cond_len_spin.setToolTip("Длина образца для клонирования голоса")
        form_layout.addRow("GPT cond len (сек):", self.gpt_cond_len_spin)
        
        # Sound norm refs
        self.sound_norm_check = QCheckBox("Авто-нормализация образца")
        self.sound_norm_check.setToolTip("Автоматическая нормализация громкости образца голоса")
        form_layout.addRow("Sound norm refs:", self.sound_norm_check)
        
        layout.addWidget(params_group)
        
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
        self.temperature_spin.setValue(self.config.get("temperature", 0.85))
        self.repetition_penalty_spin.setValue(self.config.get("repetition_penalty", 2.0))
        self.length_penalty_spin.setValue(self.config.get("length_penalty", 1.0))
        self.top_k_spin.setValue(self.config.get("top_k", 50))
        self.top_p_spin.setValue(self.config.get("top_p", 0.85))
        self.num_beams_spin.setValue(self.config.get("num_beams", 1))
        self.gpt_cond_len_spin.setValue(self.config.get("gpt_cond_len", 12))
        self.sound_norm_check.setChecked(self.config.get("sound_norm_refs", True))
    
    def on_ok(self):
        """Сохранение параметров и закрытие"""
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
        self.temperature_spin.setValue(0.85)
        self.repetition_penalty_spin.setValue(2.0)
        self.length_penalty_spin.setValue(1.0)
        self.top_k_spin.setValue(50)
        self.top_p_spin.setValue(0.85)
        self.num_beams_spin.setValue(1)
        self.gpt_cond_len_spin.setValue(12)
        self.sound_norm_check.setChecked(True)