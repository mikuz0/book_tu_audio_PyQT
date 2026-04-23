import json
import os
from pathlib import Path

class ConfigManager:
    """Управление сохранением и загрузкой конфигурации"""
    
    CONFIG_FILE = "config.json"
    
    def __init__(self):
        self.config = {
            "work_dir": "",
            "last_step": 0,
            "language": "ru",
            "window_geometry": "1000x750",
            "auto_save": True,
            "speaker": "Claribel Dervla",
            "speed": 1.0,
            "output_format": "mp3",
            "speaker_wav": "",
            "fragment_pause": 0.2,
            "initial_pause": 0.0,
            "generate_subtitles": True,
            # Параметры синтеза XTTS
            "temperature": 0.85,
            "repetition_penalty": 2.0,
            "length_penalty": 1.0,
            "top_k": 50,
            "top_p": 0.85,
            "num_beams": 1,
            "gpt_cond_len": 12,
            "sound_norm_refs": True,
            # Параметры разбиения текста
            "split_overlap": 0,  # перекрытие для сплиттера
            # Дообученная модель
            "use_finetuned_model": False,
            "finetuned_model_path": ""
        }
        self.load()
    
    def save(self):
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def load(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        if self.config.get("auto_save", True):
            self.save()
    
    def get_work_subdirs(self):
        work_dir = self.config.get("work_dir")
        if not work_dir or not os.path.exists(work_dir):
            return None
        
        work_path = Path(work_dir)
        
        dirs = {
            "source": work_path / "source",
            "extracted": work_path / "01_extracted_text",
            "replaced": work_path / "02_replaced_text",
            "fragments": work_path / "03_text_fragments",
            "audio": work_path / "04_audio",
            "subtitles": work_path / "05_subtitles",
            "config": work_path / "config"
        }
        
        for dir_path in dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        return dirs
