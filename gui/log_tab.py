#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вкладка логов выполнения
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit
from PyQt5.QtGui import QFont


class LogTab(QWidget):
    """Вкладка с логами выполнения"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Очистить лог")
        clear_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def append_log(self, message: str):
        """Добавить сообщение в лог"""
        self.log_text.append(message)
    
    def clear_log(self):
        """Очистить лог"""
        self.log_text.clear()
    
    def log_settings(self, filename: str, settings: dict):
        """
        Вывести настройки синтеза для файла в читаемом виде
        
        Args:
            filename: имя файла
            settings: словарь с настройками
        """
        self.log_text.append("")
        self.log_text.append("=" * 80)
        self.log_text.append(f"📁 Файл: {filename}")
        self.log_text.append("=" * 80)
        
        # Модель и голос
        self.log_text.append("🎙 МОДЕЛЬ И ГОЛОС:")
        if settings.get("use_finetuned_model", False):
            self.log_text.append(f"   Тип модели: ДООБУЧЕННАЯ")
            self.log_text.append(f"   Путь к модели: {settings.get('finetuned_model_path', '-')}")
        else:
            self.log_text.append(f"   Тип модели: СТАНДАРТНАЯ (XTTS-v2)")
        
        speaker = settings.get("speaker", "Claribel Dervla")
        speaker_wav = settings.get("speaker_wav", "")
        if speaker_wav:
            self.log_text.append(f"   Голос: КЛОНИРОВАНИЕ из файла: {speaker_wav}")
        else:
            self.log_text.append(f"   Голос: {speaker}")
        
        self.log_text.append("")
        self.log_text.append("⚙ ПАРАМЕТРЫ СИНТЕЗА:")
        self.log_text.append(f"   Скорость речи: {settings.get('speed', 1.0):.1f}x")
        self.log_text.append(f"   Температура: {settings.get('temperature', 0.85)}")
        self.log_text.append(f"   Штраф за повторы (repetition_penalty): {settings.get('repetition_penalty', 2.0)}")
        self.log_text.append(f"   Штраф за длину (length_penalty): {settings.get('length_penalty', 1.0)}")
        self.log_text.append(f"   Top K: {settings.get('top_k', 50)}")
        self.log_text.append(f"   Top P: {settings.get('top_p', 0.85)}")
        self.log_text.append(f"   Num Beams: {settings.get('num_beams', 1)}")
        
        # Параметры дообученной модели (если есть)
        if settings.get("use_finetuned_model", False):
            self.log_text.append("")
            self.log_text.append("🔧 ПАРАМЕТРЫ ДООБУЧЕННОЙ МОДЕЛИ:")
            self.log_text.append(f"   Длина контекста (gpt_cond_len): {settings.get('gpt_cond_len', 12)} сек")
            self.log_text.append(f"   Нормализация образца (sound_norm_refs): {settings.get('sound_norm_refs', True)}")
        
        self.log_text.append("")
        self.log_text.append("📝 ПАРАМЕТРЫ АУДИО:")
        self.log_text.append(f"   Формат: {settings.get('output_format', 'mp3').upper()}")
        self.log_text.append(f"   Пауза между фрагментами: {settings.get('fragment_pause', 0.2)} сек")
        self.log_text.append(f"   Пауза в начале: {settings.get('initial_pause', 0.0)} сек")
        self.log_text.append(f"   Субтитры: {'включены' if settings.get('generate_subtitles', True) else 'выключены'}")
        
        self.log_text.append("")
        self.log_text.append("📄 ПАРАМЕТРЫ РАЗБИЕНИЯ ТЕКСТА:")
        self.log_text.append(f"   Алгоритм: RecursiveCharacterTextSplitter")
        self.log_text.append(f"   Максимальный размер фрагмента: {settings.get('split_max_length', 250)} символов")
        self.log_text.append(f"   Перекрытие: {settings.get('split_overlap', 0)} символов")
        
        self.log_text.append("")
        self.log_text.append("📖 РАЗДЕЛИТЕЛИ:")
        self.log_text.append(f"   Приоритет: абзацы → строки → предложения (., !, ?) → запятые → пробелы")
        
        self.log_text.append("=" * 80)
        self.log_text.append("")