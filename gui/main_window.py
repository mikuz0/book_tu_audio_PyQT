#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно приложения
"""
import sys
import os
import json
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox,
    QApplication
)
from PyQt5.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_manager import ConfigManager
from gui.settings_tab import SettingsTab
from gui.process_tab import ProcessTab
from gui.log_tab import LogTab
from gui.accent_editor import AccentEditorWindow
from gui.params_dialog import ParamsDialog
from gui.split_params_dialog import SplitParamsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.program_start_time = time.time()
        
        self.init_ui()
        self.load_settings()
        
        # 🛡 Показываем окно ДО тяжёлых операций, чтобы ОС не помечала его как "зависшее"
        self.show()
        QApplication.processEvents()
        
        self.check_source_folder()
        self.refresh_task_list()
        self.raise_()
        self.activateWindow()

    def init_ui(self):
        self.setWindowTitle("Книги в аудио - Пакетный конвертер")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Вкладки
        self.settings_tab = SettingsTab(self, self.config)
        self.tab_widget.addTab(self.settings_tab, "📁 Настройки")
        self.process_tab = ProcessTab(self, self.config)
        self.tab_widget.addTab(self.process_tab, "📋 Пакетная обработка")
        self.log_tab = LogTab(self)
        self.tab_widget.addTab(self.log_tab, "📝 Лог выполнения")
        self.statusBar().showMessage("Готов к работе")

    # === Свойства для доступа к элементам из других вкладок ===
    @property
    def work_dir_edit(self):
        return self.settings_tab.work_dir_edit
    @property
    def voice_combo(self):
        return self.settings_tab.voice_combo
    @property
    def speed_slider(self):
        return self.settings_tab.speed_slider
    @property
    def mp3_radio(self):
        return self.settings_tab.mp3_radio
    @property
    def wav_radio(self):
        return self.settings_tab.wav_radio
    @property
    def speaker_wav_edit(self):
        return self.settings_tab.speaker_wav_edit
    @property
    def fragment_pause_slider(self):
        return self.settings_tab.fragment_pause_slider
    @property
    def init_pause_slider(self):
        return self.settings_tab.init_pause_slider
    @property
    def use_finetuned_radio(self):
        return self.settings_tab.use_finetuned_radio
    @property
    def finetuned_path_edit(self):
        return self.settings_tab.finetuned_path_edit
    @property
    def auto_save_check(self):
        return self.settings_tab.auto_save_check

    # === Основные методы ===
    def log(self, message: str):
        self.log_tab.append_log(message)
        QApplication.processEvents()

    def clear_log(self):
        self.log_tab.clear_log()

    def check_source_folder(self):
        work_dir = self.work_dir_edit.text()
        if work_dir and os.path.exists(work_dir):
            source_dir = Path(work_dir) / "source"
            if not source_dir.exists():
                source_dir.mkdir(parents=True, exist_ok=True)
                self.log(f"Создана папка для исходных файлов: {source_dir}")
                self.log("Поместите книги (PDF, EPUB, FB2, TXT) в эту папку")

    def refresh_task_list(self):
        """Обновить список заданий"""
        work_dir = self.work_dir_edit.text()
        if not work_dir or not os.path.exists(work_dir):
            return
        output_format = "mp3" if self.mp3_radio.isChecked() else "wav"
        self.process_tab.load_tasks(work_dir, output_format)
        self.log(f"Обновлен список заданий: {len(self.process_tab.task_manager.tasks)} файлов")

    def open_audio_folder(self):
        work_dir = self.work_dir_edit.text()
        if work_dir:
            audio_dir = Path(work_dir) / "04_audio"
            if audio_dir.exists():
                import subprocess
                subprocess.Popen(['xdg-open', str(audio_dir)])
            else:
                QMessageBox.warning(self, "Ошибка", f"Папка не найдена: {audio_dir}")

    # === Диалоги ===
    def open_stress_dict(self):
        work_dir = self.work_dir_edit.text()
        if not work_dir:
            QMessageBox.critical(self, "Ошибка", "Сначала выберите рабочую папку!")
            return
        dict_file = Path(work_dir) / "config" / "stress_dict.json"
        self.editor_window = AccentEditorWindow(str(dict_file))
        self.editor_window.show()

    def create_example_dict(self):
        work_dir = self.work_dir_edit.text()
        if not work_dir:
            QMessageBox.critical(self, "Ошибка", "Сначала выберите рабочую папку!")
            return
        dict_file = Path(work_dir) / "config" / "stress_dict.json"
        if dict_file.exists():
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Файл {dict_file.name} уже существует.\nПерезаписать?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        example = {"препод+обный": "преподо+бный", "+авва": "а+вва", "Господ+а": "Г+оспода"}
        try:
            dict_file.parent.mkdir(parents=True, exist_ok=True)
            with open(dict_file, 'w', encoding='utf-8') as f:
                json.dump(example, f, ensure_ascii=False, indent=2)
            self.log(f"Создан пример словаря: {dict_file}")
            QMessageBox.information(self, "Успех", f"Создан пример словаря:\n{dict_file}")
        except Exception as e:
            self.log(f"Ошибка создания словаря: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать словарь: {e}")

    def open_synth_params(self):
        dialog = ParamsDialog(self, self.config)
        dialog.exec_()

    def open_split_params(self):
        dialog = SplitParamsDialog(self, self.config)
        dialog.exec_()

    def save_current_settings(self):
        self.settings_tab.save_settings()
        self.config.set("auto_save", self.auto_save_check.isChecked())

    def load_settings(self):
        self.settings_tab.load_settings()

    def closeEvent(self, event):
        if self.process_tab.queue_worker and self.process_tab.queue_worker.isRunning():
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Идет обработка очереди. Прервать и выйти?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.process_tab.queue_worker.stop()
                self.process_tab.queue_worker.wait()
            else:
                event.ignore()
                return
        if self.auto_save_check.isChecked():
            self.save_current_settings()
        self.config.set("window_geometry", f"{self.width()}x{self.height()}")
        self.config.save()
        event.accept()