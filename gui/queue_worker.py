#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поток для последовательной обработки очереди файлов
"""
import shutil
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from core.text_extractor import TextExtractor
from core.text_processor import TextProcessor
from core.audio_generator import AudioGenerator


class QueueWorker(QThread):
    """Поток для последовательной обработки очереди файлов"""
    progress = pyqtSignal(int, int, str, str)
    log = pyqtSignal(str)
    file_finished = pyqtSignal(str, bool, str)
    finished = pyqtSignal()

    def __init__(self, work_dir: str, files_to_process: list, config_settings: dict):
        super().__init__()
        self.work_dir = work_dir
        self.files_to_process = files_to_process
        self.config_settings = config_settings
        self._is_running = True
        self._is_paused = False

    def _log_settings(self, filename: str):
        """Вывести настройки синтеза в лог"""
        settings = self.config_settings
        
        self.log.emit(f"\n{'='*80}")
        self.log.emit(f"📁 ФАЙЛ: {filename}")
        self.log.emit(f"{'='*80}")
        
        # Модель и голос
        use_finetuned = settings.get("use_finetuned_model", False)
        if use_finetuned:
            self.log.emit(f"🎙 МОДЕЛЬ: ДООБУЧЕННАЯ")
            self.log.emit(f"   Путь: {settings.get('finetuned_model_path', '-')}")
        else:
            self.log.emit(f"🎙 МОДЕЛЬ: СТАНДАРТНАЯ (XTTS-v2)")
        
        speaker = settings.get("speaker", "Claribel Dervla")
        speaker_wav = settings.get("speaker_wav", "")
        if speaker_wav:
            self.log.emit(f"   Голос: КЛОНИРОВАНИЕ из файла: {speaker_wav}")
        else:
            self.log.emit(f"   Голос: {speaker}")
        
        self.log.emit("")
        self.log.emit("⚙ ПАРАМЕТРЫ СИНТЕЗА:")
        self.log.emit(f"   Скорость речи: {settings.get('speed', 1.0):.1f}x")
        self.log.emit(f"   Температура: {settings.get('temperature', 0.85)}")
        self.log.emit(f"   Штраф за повторы: {settings.get('repetition_penalty', 2.0)}")
        self.log.emit(f"   Штраф за длину: {settings.get('length_penalty', 1.0)}")
        self.log.emit(f"   Top K: {settings.get('top_k', 50)}")
        self.log.emit(f"   Top P: {settings.get('top_p', 0.85)}")
        self.log.emit(f"   Num Beams: {settings.get('num_beams', 1)}")
        
        if use_finetuned:
            self.log.emit("")
            self.log.emit("🔧 ПАРАМЕТРЫ ДООБУЧЕННОЙ МОДЕЛИ:")
            self.log.emit(f"   Длина контекста (gpt_cond_len): {settings.get('gpt_cond_len', 12)} сек")
            self.log.emit(f"   Нормализация образца: {settings.get('sound_norm_refs', True)}")
        
        self.log.emit("")
        self.log.emit("📝 ПАРАМЕТРЫ АУДИО:")
        self.log.emit(f"   Формат: {settings.get('output_format', 'mp3').upper()}")
        self.log.emit(f"   Пауза между фрагментами: {settings.get('fragment_pause', 0.2)} сек")
        self.log.emit(f"   Пауза в начале: {settings.get('initial_pause', 0.0)} сек")
        self.log.emit(f"   Субтитры: включены")
        
        self.log.emit("")
        self.log.emit("📄 ПАРАМЕТРЫ РАЗБИЕНИЯ ТЕКСТА:")
        self.log.emit(f"   Алгоритм: RecursiveCharacterTextSplitter")
        self.log.emit(f"   Максимальный размер фрагмента: {settings.get('split_max_length', 250)} символов")
        self.log.emit(f"   Перекрытие: {settings.get('split_overlap', 0)} символов")
        self.log.emit(f"   Приоритет разделителей: абзацы → строки → предложения → запятые → пробелы")
        
        self.log.emit(f"{'='*80}\n")

    def _process_single_file(self, file_path: Path, idx: int, total: int, filename: str) -> bool:
        """Обработать один файл"""
        
        # 🔹 Логируем настройки перед началом
        self._log_settings(filename)
        
        # Этап 1: Извлечение текста
        self.progress.emit(idx, total, filename, "1/4 Извлечение текста...")
        extractor = TextExtractor(self.work_dir)
        source_dir = Path(self.work_dir) / "source"
        if not source_dir.exists():
            source_dir.mkdir(parents=True, exist_ok=True)
        
        source_file = source_dir / filename
        if not source_file.exists():
            shutil.copy2(file_path, source_file)
        extracted_file = extractor.extract(source_file)

        # Этап 2: Обработка текста (ударения)
        self.progress.emit(idx, total, filename, "2/4 Обработка текста (ударения)...")
        processor = TextProcessor(self.work_dir)
        processed_file = processor.process_file(extracted_file)

        # Этап 3: Разбиение на фрагменты
        self.progress.emit(idx, total, filename, "3/4 Разбиение на фрагменты...")
        chunk_size = self.config_settings.get("split_max_length", 250)
        chunk_overlap = self.config_settings.get("split_overlap", 0)
        processor.split_file(processed_file, chunk_size, chunk_overlap)

        # Этап 4: Генерация аудио
        self.progress.emit(idx, total, filename, "4/4 Генерация аудио...")
        
        def on_fragment_progress(fname, pct, chars_done, chars_total):
            stage = f"Генерация: {pct}% ({chars_done}/{chars_total} симв.)"
            self.progress.emit(idx, total, filename, stage)
        
        generator = AudioGenerator(
            self.work_dir,
            speaker=self.config_settings.get("speaker", "Claribel Dervla"),
            speed=self.config_settings.get("speed", 1.0),
            output_format=self.config_settings.get("output_format", "mp3"),
            speaker_wav=self.config_settings.get("speaker_wav", "") or None,
            fragment_pause=self.config_settings.get("fragment_pause", 0.2),
            initial_pause=self.config_settings.get("initial_pause", 0.0),
            generate_subtitles=True,
            temperature=self.config_settings.get("temperature", 0.85),
            repetition_penalty=self.config_settings.get("repetition_penalty", 2.0),
            length_penalty=self.config_settings.get("length_penalty", 1.0),
            top_k=self.config_settings.get("top_k", 50),
            top_p=self.config_settings.get("top_p", 0.85),
            num_beams=self.config_settings.get("num_beams", 1),
            gpt_cond_len=self.config_settings.get("gpt_cond_len", 12),
            sound_norm_refs=self.config_settings.get("sound_norm_refs", True),
            use_finetuned_model=self.config_settings.get("use_finetuned_model", False),
            finetuned_model_path=self.config_settings.get("finetuned_model_path", ""),
            progress_callback=on_fragment_progress
        )
        
        audio_file, subtitle_file = generator.generate_single_file(filename, progress_callback=on_fragment_progress)
        
        if audio_file is None:
            raise Exception(f"Не удалось сгенерировать аудио для {filename}")
        return True

    def run(self):
        total = len(self.files_to_process)
        for idx, file_path in enumerate(self.files_to_process, 1):
            if not self._is_running:
                break
            while self._is_paused and self._is_running:
                self.msleep(100)
            filename = file_path.name
            try:
                success = self._process_single_file(file_path, idx, total, filename)
                if success:
                    self.file_finished.emit(filename, True, "")
                else:
                    self.file_finished.emit(filename, False, "Неизвестная ошибка")
            except Exception as e:
                error_msg = str(e)
                self.file_finished.emit(filename, False, error_msg)
                self.log.emit(f"❌ Ошибка при обработке {filename}: {error_msg}")
        self.finished.emit()

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def stop(self):
        self._is_running = False
        self._is_paused = False