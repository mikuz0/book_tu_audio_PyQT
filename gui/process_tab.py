#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вкладка пакетной обработки
"""
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QProgressBar, QLabel, QMessageBox, QTabWidget, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont
from gui.task_manager import TaskManager
from gui.queue_worker import QueueWorker

class ProcessTab(QWidget):
    """Вкладка пакетной обработки"""
    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.task_manager = TaskManager()
        self.queue_worker = None
        self.selected_filename = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # === Верхняя панель: управление очередью ===
        queue_group = QGroupBox("Пакетная обработка")
        queue_layout = QVBoxLayout(queue_group)

        # Кнопки управления
        controls_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Обновить список")
        self.refresh_btn.clicked.connect(self.parent.refresh_task_list)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addSpacing(20)
        self.select_all_btn = QPushButton("✓ Выбрать всё")
        self.select_all_btn.clicked.connect(self.select_all)
        controls_layout.addWidget(self.select_all_btn)
        self.select_unready_btn = QPushButton("⚠ Выбрать невыполненные")
        self.select_unready_btn.clicked.connect(self.select_unready)
        controls_layout.addWidget(self.select_unready_btn)
        self.select_errors_btn = QPushButton("❌ Выбрать ошибочные")
        self.select_errors_btn.clicked.connect(self.select_errors)
        controls_layout.addWidget(self.select_errors_btn)
        self.clear_selection_btn = QPushButton("✗ Снять выделение")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        controls_layout.addWidget(self.clear_selection_btn)
        controls_layout.addStretch()
        queue_layout.addLayout(controls_layout)

        # Кнопки запуска/остановки
        queue_controls_layout = QHBoxLayout()
        self.start_queue_btn = QPushButton("▶ Запуск")
        self.start_queue_btn.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
        self.start_queue_btn.clicked.connect(self.start_queue)
        queue_controls_layout.addWidget(self.start_queue_btn)
        self.pause_queue_btn = QPushButton("⏸ Пауза")
        self.pause_queue_btn.setEnabled(False)
        self.pause_queue_btn.clicked.connect(self.pause_queue)
        queue_controls_layout.addWidget(self.pause_queue_btn)
        self.stop_queue_btn = QPushButton("⏹ Стоп")
        self.stop_queue_btn.setEnabled(False)
        self.stop_queue_btn.setStyleSheet("background-color: #f44336; font-weight: bold;")
        self.stop_queue_btn.clicked.connect(self.stop_queue)
        queue_controls_layout.addWidget(self.stop_queue_btn)
        self.retry_errors_btn = QPushButton("🔄 Повторить ошибки")
        self.retry_errors_btn.clicked.connect(self.retry_errors)
        queue_controls_layout.addWidget(self.retry_errors_btn)
        queue_controls_layout.addStretch()
        queue_layout.addLayout(queue_controls_layout)

        # Таблица заданий
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels(["", "Статус", "Имя файла", "Аудио", "Ошибка"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tasks_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tasks_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.itemClicked.connect(self.on_task_selected)
        self.tasks_table.itemChanged.connect(self.on_checkbox_changed)
        queue_layout.addWidget(self.tasks_table)

        # Прогресс
        self.queue_progress = QProgressBar()
        self.queue_progress.setVisible(False)
        queue_layout.addWidget(self.queue_progress)
        self.queue_status_label = QLabel("")
        self.queue_status_label.setStyleSheet("font-weight: bold;")
        queue_layout.addWidget(self.queue_status_label)

        layout.addWidget(queue_group)

        # === Нижняя панель: просмотр промежуточных файлов ===
        preview_group = QGroupBox("Просмотр промежуточных файлов (выбранный файл)")
        preview_layout = QVBoxLayout(preview_group)

        # Выбранный файл
        selected_layout = QHBoxLayout()
        selected_layout.addWidget(QLabel("Файл:"))
        self.selected_file_label = QLabel("(не выбран)")
        self.selected_file_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        selected_layout.addWidget(self.selected_file_label)
        selected_layout.addStretch()

        # Кнопки открытия папок
        self.open_extracted_btn = QPushButton("📄 Открыть извлечённый текст")
        self.open_extracted_btn.clicked.connect(self.open_extracted_folder)
        self.open_extracted_btn.setEnabled(False)
        selected_layout.addWidget(self.open_extracted_btn)

        self.open_replaced_btn = QPushButton("✏ Открыть обработанный текст")
        self.open_replaced_btn.clicked.connect(self.open_replaced_folder)
        self.open_replaced_btn.setEnabled(False)
        selected_layout.addWidget(self.open_replaced_btn)

        self.open_fragments_btn = QPushButton("📑 Открыть фрагменты")
        self.open_fragments_btn.clicked.connect(self.open_fragments_folder)
        self.open_fragments_btn.setEnabled(False)
        selected_layout.addWidget(self.open_fragments_btn)

        self.open_audio_btn = QPushButton("🎵 Открыть аудио")
        self.open_audio_btn.clicked.connect(self.parent.open_audio_folder)
        self.open_audio_btn.setEnabled(False)
        selected_layout.addWidget(self.open_audio_btn)

        preview_layout.addLayout(selected_layout)

        # Вкладки для просмотра содержимого
        self.preview_tabs = QTabWidget()

        # Вкладка с извлечённым текстом
        self.extracted_text = QTextEdit()
        self.extracted_text.setReadOnly(True)
        self.extracted_text.setFont(QFont("Consolas", 10))
        self.preview_tabs.addTab(self.extracted_text, "Извлечённый текст")

        # Вкладка с обработанным текстом
        self.replaced_text = QTextEdit()
        self.replaced_text.setReadOnly(True)
        self.replaced_text.setFont(QFont("Consolas", 10))
        self.preview_tabs.addTab(self.replaced_text, "Обработанный текст (ударения)")

        # Вкладка со списком фрагментов
        self.fragments_list = QTextEdit()
        self.fragments_list.setReadOnly(True)
        self.fragments_list.setFont(QFont("Consolas", 9))
        self.preview_tabs.addTab(self.fragments_list, "Фрагменты")

        preview_layout.addWidget(self.preview_tabs)
        layout.addWidget(preview_group)

    def update_tasks_table(self):
        """Обновить таблицу заданий"""
        work_dir = self.parent.work_dir_edit.text()
        output_format = "mp3" if self.parent.mp3_radio.isChecked() else "wav"
        self.tasks_table.blockSignals(True)
        self.tasks_table.setRowCount(len(self.task_manager.tasks))
        for row, (filename, task) in enumerate(self.task_manager.tasks.items()):
            # Чекбокс
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Checked if task.checked else Qt.Unchecked)
            checkbox.setData(Qt.UserRole, filename)
            self.tasks_table.setItem(row, 0, checkbox)

            # Статус
            icon, text = self.task_manager.get_status_info(filename)
            status_item = QTableWidgetItem(f"{icon} {text}")
            self.tasks_table.setItem(row, 1, status_item)

            # Имя файла
            name_item = QTableWidgetItem(filename)
            self.tasks_table.setItem(row, 2, name_item)

            # Аудио
            if task.status == "completed":
                duration = task.get_audio_duration(Path(work_dir), output_format)
                audio_item = QTableWidgetItem(f"✅ {duration}" if duration else "✅ Да")
            else:
                audio_item = QTableWidgetItem("❌ Нет")
            self.tasks_table.setItem(row, 3, audio_item)

            # Ошибка
            error_item = QTableWidgetItem(task.error)
            self.tasks_table.setItem(row, 4, error_item)

            # Цвет строки
            color = self._get_row_color(task.status)
            for col in range(5):
                item = self.tasks_table.item(row, col)
                if item:
                    item.setBackground(QBrush(color))
        self.tasks_table.blockSignals(False)

    def _get_row_color(self, status: str) -> QColor:
        """Получить цвет строки в зависимости от статуса"""
        if status == "completed":
            return QColor(200, 230, 200)
        elif status == "error":
            return QColor(255, 200, 200)
        elif status == "processing":
            return QColor(255, 255, 180)
        return QColor(255, 255, 255)

    def on_checkbox_changed(self, item):
        """Обработка изменения чекбокса"""
        if item.column() == 0:
            filename = item.data(Qt.UserRole)
            if filename:
                checked = item.checkState() == Qt.Checked
                self.task_manager.update_check_state(filename, checked)

    def on_task_selected(self, item):
        """Выбор файла в таблице"""
        row = item.row()
        filename_item = self.tasks_table.item(row, 2)
        if filename_item:
            filename = filename_item.text()
            if filename in self.task_manager.tasks:
                self.selected_filename = filename
                self.selected_file_label.setText(filename)
                self.load_preview_files(filename)
                # Включаем кнопки
                self.open_extracted_btn.setEnabled(True)
                self.open_replaced_btn.setEnabled(True)
                self.open_fragments_btn.setEnabled(True)
                self.open_audio_btn.setEnabled(True)

    def load_preview_files(self, filename: str):
        """Загрузить промежуточные файлы для просмотра"""
        work_dir = self.parent.work_dir_edit.text()
        if not work_dir:
            return
        stem = Path(filename).stem

        # 🔹 ИЗМЕНЕНО: Пробуем разные варианты для папки с фрагментами
        possible_fragments_folders = [
            Path(work_dir) / "03_text_fragments" / f"{stem}_replaced",
            Path(work_dir) / "03_text_fragments" / f"{stem}_extracted_replaced",
            Path(work_dir) / "03_text_fragments" / stem,
        ]
        fragments_dir = None
        for folder in possible_fragments_folders:
            if folder.exists():
                fragments_dir = folder
                break

        # Извлечённый текст
        extracted_path = Path(work_dir) / "01_extracted_text" / f"{stem}_extracted.txt"
        if extracted_path.exists():
            with open(extracted_path, 'r', encoding='utf-8') as f:
                self.extracted_text.setText(f.read())
        else:
            self.extracted_text.setText("(файл не найден)")

        # 🔹 ИЗМЕНЕНО: Обработанный текст — пробуем оба варианта имени файла
        possible_replaced_files = [
            Path(work_dir) / "02_replaced_text" / f"{stem}_replaced.txt",
            Path(work_dir) / "02_replaced_text" / f"{stem}_extracted_replaced.txt",
        ]
        replaced_path = None
        for path in possible_replaced_files:
            if path.exists():
                replaced_path = path
                break

        if replaced_path:
            with open(replaced_path, 'r', encoding='utf-8') as f:
                self.replaced_text.setText(f.read())
        else:
            self.replaced_text.setText("(файл не найден)")

        # Фрагменты
        if fragments_dir and fragments_dir.exists():
            fragments = sorted(fragments_dir.glob("fragment_*.txt"))
            if fragments:
                text = ""
                for frag_file in fragments:
                    with open(frag_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    text += f"{frag_file.name}:\n{content}\n{'-'*50}\n"
                self.fragments_list.setText(text)
            else:
                self.fragments_list.setText("(нет фрагментов)")
        else:
            self.fragments_list.setText("(папка с фрагментами не найдена)")

    def open_extracted_folder(self):
        """Открыть папку с извлечёнными текстами"""
        if hasattr(self, 'selected_filename') and self.selected_filename:
            work_dir = self.parent.work_dir_edit.text()
            if work_dir:
                folder = Path(work_dir) / "01_extracted_text"
                if folder.exists():
                    import subprocess
                    subprocess.Popen(['xdg-open', str(folder)])

    def open_replaced_folder(self):
        """Открыть папку с обработанными текстами"""
        if hasattr(self, 'selected_filename') and self.selected_filename:
            work_dir = self.parent.work_dir_edit.text()
            if work_dir:
                folder = Path(work_dir) / "02_replaced_text"
                if folder.exists():
                    import subprocess
                    subprocess.Popen(['xdg-open', str(folder)])

    def open_fragments_folder(self):
        """Открыть папку с фрагментами выбранного файла"""
        if hasattr(self, 'selected_filename') and self.selected_filename:
            work_dir = self.parent.work_dir_edit.text()
            if work_dir:
                stem = Path(self.selected_filename).stem
                # 🔹 ИЗМЕНЕНО: Пробуем разные варианты
                possible_folders = [
                    Path(work_dir) / "03_text_fragments" / f"{stem}_replaced",
                    Path(work_dir) / "03_text_fragments" / f"{stem}_extracted_replaced",
                    Path(work_dir) / "03_text_fragments" / stem,
                ]
                for folder in possible_folders:
                    if folder.exists():
                        import subprocess
                        subprocess.Popen(['xdg-open', str(folder)])
                        break

    def select_all(self):
        """Выбрать все задания"""
        self.task_manager.select_all()
        self.update_tasks_table()

    def select_unready(self):
        """Выбрать невыполненные задания"""
        self.task_manager.select_unready()
        self.update_tasks_table()

    def select_errors(self):
        """Выбрать задания с ошибками"""
        self.task_manager.select_errors()
        self.update_tasks_table()

    def clear_selection(self):
        """Снять выделение"""
        self.task_manager.clear_selection()
        self.update_tasks_table()

    def start_queue(self):
        """Запустить обработку очереди"""
        work_dir = self.parent.work_dir_edit.text()
        if not work_dir:
            QMessageBox.critical(self, "Ошибка", "Выберите рабочую папку!")
            return
        selected_files = self.task_manager.get_selected_files(Path(work_dir))
        if not selected_files:
            QMessageBox.information(self, "Очередь", "Нет выбранных файлов для обработки")
            return

        # Сохраняем настройки
        self.parent.save_current_settings()

        # Получаем настройки
        settings_tab = self.parent.settings_tab
        config_settings = {
            "split_min_length": self.config.get("split_min_length", 150),
            "split_max_length": self.config.get("split_max_length", 250),
            "split_primary_delimiters": self.config.get("split_primary_delimiters", ".!?"),
            "split_secondary_delimiters": self.config.get("split_secondary_delimiters", ":;"),
            "split_terminator": self.config.get("split_terminator", "."),
            **settings_tab.get_settings(),
            "temperature": self.config.get("temperature", 0.85),
            "repetition_penalty": self.config.get("repetition_penalty", 2.0),
            "length_penalty": self.config.get("length_penalty", 1.0),
            "top_k": self.config.get("top_k", 50),
            "top_p": self.config.get("top_p", 0.85),
            "num_beams": self.config.get("num_beams", 1),
            "gpt_cond_len": self.config.get("gpt_cond_len", 12),
            "sound_norm_refs": self.config.get("sound_norm_refs", True),
        }

        # Отмечаем выбранные файлы как queued
        for file_path in selected_files:
            filename = file_path.name
            if filename in self.task_manager.tasks:
                if self.task_manager.tasks[filename].status != "completed":
                    self.task_manager.mark_queued(filename)
        self.update_tasks_table()

        # Запускаем поток
        self.queue_worker = QueueWorker(work_dir, selected_files, config_settings)
        self.queue_worker.progress.connect(self.on_queue_progress)
        self.queue_worker.log.connect(self.parent.log)
        self.queue_worker.file_finished.connect(self.on_file_finished)
        self.queue_worker.finished.connect(self.on_queue_finished)
        self.queue_worker.start()

        # Обновляем UI
        self._set_queue_ui_enabled(True)
        self.queue_progress.setVisible(True)
        self.queue_progress.setRange(0, len(selected_files))
        self.queue_progress.setValue(0)
        self.parent.log("=" * 50)
        self.parent.log(f"ЗАПУСК ОЧЕРЕДИ: {len(selected_files)} файлов")
        self.parent.log("=" * 50)

    def _set_queue_ui_enabled(self, running: bool):
        """Включить/выключить UI очереди"""
        self.start_queue_btn.setEnabled(not running)
        self.pause_queue_btn.setEnabled(running)
        self.stop_queue_btn.setEnabled(running)
        self.refresh_btn.setEnabled(not running)
        self.select_all_btn.setEnabled(not running)
        self.select_unready_btn.setEnabled(not running)
        self.select_errors_btn.setEnabled(not running)
        self.clear_selection_btn.setEnabled(not running)
        self.retry_errors_btn.setEnabled(not running)
        if not running:
            self.start_queue_btn.setText("▶ Запуск")
            self.pause_queue_btn.setEnabled(False)
            self.stop_queue_btn.setEnabled(False)

    def pause_queue(self):
        """Поставить очередь на паузу"""
        if self.queue_worker:
            self.queue_worker.pause()
            self.pause_queue_btn.setEnabled(False)
            self.start_queue_btn.setEnabled(True)
            self.start_queue_btn.setText("▶ Возобновить")
            self.parent.log("⏸ Очередь поставлена на паузу")

    def stop_queue(self):
        """Остановить очередь"""
        if self.queue_worker:
            self.queue_worker.stop()
            self.queue_worker.wait()
            self.queue_worker = None
            self.task_manager.reset_queued_and_processing()
            self.update_tasks_table()
            self._set_queue_ui_enabled(False)
            self.queue_progress.setVisible(False)
            self.queue_status_label.setText("")
            self.parent.log("⏹ Очередь остановлена")

    def retry_errors(self):
        """Повторить задания с ошибками"""
        self.task_manager.reset_errors()
        self.update_tasks_table()
        self.start_queue()

    def on_queue_progress(self, current, total, filename, stage):
        """Обновление прогресса очереди"""
        self.queue_progress.setMaximum(total)

        # 🔹 ИЗМЕНЕНО: Если stage содержит символы, парсим для точного прогресса
        if "Генерация:" in stage and "симв." in stage:
            # Прогресс внутри файла: показываем как есть, не меняем значение прогресс-бара
            pass
        else:
            # Обычный прогресс по файлам
            self.queue_progress.setValue(current - 1)

        self.queue_status_label.setText(f"Обработка: {filename} - {stage}")
        self.task_manager.mark_processing(filename)
        self.update_tasks_table()

        # Обновляем просмотр, если это выбранный файл
        if hasattr(self, 'selected_filename') and self.selected_filename == filename:
            self.load_preview_files(filename)

    def on_file_finished(self, filename, success, error_message):
        """Завершение обработки одного файла"""
        if success:
            self.task_manager.mark_completed(filename)
            self.parent.log(f"✅ {filename} - обработан успешно")
        else:
            self.task_manager.mark_error(filename, error_message)
            self.parent.log(f"❌ {filename} - ошибка: {error_message}")
        self.update_tasks_table()

        # Обновляем просмотр, если это выбранный файл
        if hasattr(self, 'selected_filename') and self.selected_filename == filename:
            self.load_preview_files(filename)

        completed = self.task_manager.get_counts()["completed"]
        self.queue_progress.setValue(completed)

    def on_queue_finished(self):
        """Завершение обработки очереди"""
        self.queue_worker = None
        self._set_queue_ui_enabled(False)
        self.queue_progress.setVisible(False)
        self.queue_status_label.setText("")
        counts = self.task_manager.get_counts()
        self.parent.log("=" * 50)
        self.parent.log(f"ОЧЕРЕДЬ ЗАВЕРШЕНА: успешно {counts['completed']}, ошибок {counts['error']}")
        self.parent.log("=" * 50)
        if counts["error"] > 0:
            QMessageBox.warning(self, "Очередь завершена",
                f"Обработка завершена.\nУспешно: {counts['completed']}\nОшибок: {counts['error']}\nНажмите 'Повторить ошибки' для повторной обработки.")
        else:
            QMessageBox.information(self, "Очередь завершена",
                f"Все выбранные файлы успешно обработаны!\nОбработано: {counts['completed']}")
        self.parent.refresh_task_list()

    def load_tasks(self, work_dir: str, output_format: str):
        """Загрузить задания из папки source"""
        source_dir = Path(work_dir) / "source"
        self.task_manager.load_from_source(source_dir, Path(work_dir), output_format)
        self.update_tasks_table()