import os
from pathlib import Path

def ensure_dir(path):
    """Создать директорию, если она не существует"""
    Path(path).mkdir(parents=True, exist_ok=True)

def get_file_size(file_path):
    """Получить размер файла в читаемом формате"""
    size = os.path.getsize(file_path)
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} ТБ"