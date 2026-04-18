import json
import re
from pathlib import Path

class StressDictionary:
    """Словарь для исправления ударений"""
    
    def __init__(self, work_dir):
        self.work_dir = Path(work_dir)
        self.config_dir = self.work_dir / "config"
        self.config_dir.mkdir(exist_ok=True)
        self.dict_file = self.config_dir / "stress_dict.json"
        self.dictionary = {}
        self.load()
    
    def load(self):
        if self.dict_file.exists():
            try:
                with open(self.dict_file, 'r', encoding='utf-8') as f:
                    self.dictionary = json.load(f)
                print(f"Загружено {len(self.dictionary)} исправлений")
            except Exception as e:
                print(f"Ошибка загрузки словаря: {e}")
                self.dictionary = {}
        else:
            print("Файл словаря не найден")
    
    def save(self):
        try:
            with open(self.dict_file, 'w', encoding='utf-8') as f:
                json.dump(self.dictionary, f, ensure_ascii=False, indent=2)
            print(f"Словарь сохранён: {self.dict_file}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def apply(self, text):
        """Применить исправления из словаря к тексту"""
        if not self.dictionary:
            return text
        
        result = text
        for wrong, correct in sorted(self.dictionary.items(), key=lambda x: len(x[0]), reverse=True):
            result = result.replace(wrong, correct)
        return result
    
    def create_example(self, overwrite=False):
        """Создать пример словаря"""
        if self.dict_file.exists() and not overwrite:
            print(f"Файл {self.dict_file} уже существует. Используйте overwrite=True для перезаписи.")
            return False
        
        example = {
            "препод+обный": "преподо+бный",
            "+авва": "а+вва",
            "Господ+а": "Г+оспода"
        }
        self.dictionary = example
        self.save()
        return True
    
    def get_dictionary(self):
        return self.dictionary