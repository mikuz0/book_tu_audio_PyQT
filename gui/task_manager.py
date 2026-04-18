#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Управление заданиями (список файлов, статусы)
"""
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TaskItem:
    """Класс для хранения информации о задании"""
    file_path: Path
    status: str = "waiting"  # waiting, queued, processing, completed, error
    error: str = ""
    checked: bool = False

    def get_display_name(self) -> str:
        return self.file_path.name

    def get_audio_path(self, work_dir: Path, output_format: str = "mp3") -> Path:
        audio_dir = work_dir / "04_audio"
        stem = self.file_path.stem
        return audio_dir / f"{stem}.{output_format}"

    def check_audio_exists(self, work_dir: Path, output_format: str = "mp3") -> bool:
        audio_path = self.get_audio_path(work_dir, output_format)
        return audio_path.exists()

    def get_audio_duration(self, work_dir: Path, output_format: str = "mp3") -> str:
        audio_path = self.get_audio_path(work_dir, output_format)
        if not audio_path.exists():
            return ""
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                   '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)]
            # Добавлен timeout, чтобы ffprobe не вешал поток при повреждённых файлах
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            duration = float(result.stdout)
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}:{seconds:02d}"
        except Exception:
            return "Да"

class TaskManager:
    """Менеджер заданий"""
    STATUS_ICONS = {
        "waiting": "⚪",
        "queued": "🟡",
        "processing": "🔵",
        "completed": "🟢",
        "error": "🔴"
    }
    STATUS_TEXT = {
        "waiting": "Ожидает",
        "queued": "В очереди",
        "processing": "В работе",
        "completed": "Готово",
        "error": "Ошибка"
    }

    def __init__(self):
        self.tasks: Dict[str, TaskItem] = {}

    def load_from_source(self, source_dir: Path, work_dir: Path, output_format: str = "mp3"):
        """Загрузить задания из папки source"""
        if not source_dir.exists():
            source_dir.mkdir(parents=True, exist_ok=True)
            self.tasks = {}
            return
            
        supported_ext = ['.txt', '.pdf', '.epub', '.fb2']
        all_files = []
        
        # 1. Собираем все поддерживаемые файлы
        for ext in supported_ext:
            all_files.extend(source_dir.glob(f"*{ext}"))
            
        # 2. Оставляем только файлы и сортируем по имени (лексикографически)
        all_files = [f for f in all_files if f.is_file()]
        all_files.sort(key=lambda p: p.name)
        
        # 3. Формируем новый словарь заданий в отсортированном порядке
        new_tasks = {}
        for file_path in all_files:
            filename = file_path.name
            if filename in self.tasks:
                task = self.tasks[filename]
                # Сохраняем статус, если файл уже был в списке
                if task.check_audio_exists(work_dir, output_format):
                    if task.status not in ["processing", "queued"]:
                        task.status = "completed"
                else:
                    if task.status == "completed":
                        task.status = "waiting"
                new_tasks[filename] = task
            else:
                task = TaskItem(file_path)
                if task.check_audio_exists(work_dir, output_format):
                    task.status = "completed"
                new_tasks[filename] = task
                
        self.tasks = new_tasks

    def get_selected_files(self, work_dir: Path) -> List[Path]:
        """Получить список выбранных файлов для обработки"""
        source_dir = work_dir / "source"
        if not source_dir.exists():
            return []
        selected = []
        for filename, task in self.tasks.items():
            # Выбираем только отмеченные и не выполненные/не в обработке
            if task.checked and task.status not in ["processing", "queued", "completed"]:
                file_path = source_dir / filename
                if file_path.exists():
                    selected.append(file_path)
        return selected

    def update_check_state(self, filename: str, checked: bool):
        """Обновить состояние чекбокса задания"""
        if filename in self.tasks:
            self.tasks[filename].checked = checked

    def select_all(self):
        """Выбрать все задания"""
        for task in self.tasks.values():
            task.checked = True

    def select_unready(self):
        """Выбрать невыполненные задания (ожидают и ошибки)"""
        for task in self.tasks.values():
            task.checked = task.status in ["waiting", "error"]

    def select_errors(self):
        """Выбрать задания с ошибками"""
        for task in self.tasks.values():
            task.checked = task.status == "error"

    def clear_selection(self):
        """Снять выделение со всех заданий"""
        for task in self.tasks.values():
            task.checked = False

    def mark_queued(self, filename: str):
        """Отметить задание как поставленное в очередь"""
        if filename in self.tasks and self.tasks[filename].status == "waiting":
            self.tasks[filename].status = "queued"

    def mark_processing(self, filename: str):
        """Отметить задание как обрабатываемое"""
        if filename in self.tasks:
            self.tasks[filename].status = "processing"

    def mark_completed(self, filename: str):
        """Отметить задание как завершённое"""
        if filename in self.tasks:
            self.tasks[filename].status = "completed"
            self.tasks[filename].error = ""

    def mark_error(self, filename: str, error_msg: str):
        """Отметить задание как ошибочное"""
        if filename in self.tasks:
            self.tasks[filename].status = "error"
            self.tasks[filename].error = error_msg[:200]  # Ограничиваем длину ошибки

    def reset_queued_and_processing(self):
        """Сбросить статусы queued и processing в waiting"""
        for task in self.tasks.values():
            if task.status in ["queued", "processing"]:
                task.status = "waiting"

    def reset_errors(self):
        """Сбросить статусы error в waiting и снять ошибки"""
        for task in self.tasks.values():
            if task.status == "error":
                task.status = "waiting"
                task.error = ""
                task.checked = True

    def get_counts(self) -> dict:
        """Получить статистику по статусам"""
        counts = {"total": len(self.tasks), "completed": 0, "error": 0, "waiting": 0}
        for task in self.tasks.values():
            if task.status == "completed":
                counts["completed"] += 1
            elif task.status == "error":
                counts["error"] += 1
            elif task.status in ["waiting", "queued", "processing"]:
                counts["waiting"] += 1
        return counts

    def get_status_info(self, filename: str) -> tuple:
        """Получить иконку и текст статуса для задания"""
        if filename not in self.tasks:
            return "⚪", "Ожидает"
        task = self.tasks[filename]
        icon = self.STATUS_ICONS.get(task.status, "⚪")
        text = self.STATUS_TEXT.get(task.status, "Ожидает")
        return icon, text