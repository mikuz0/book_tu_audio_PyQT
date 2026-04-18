import os
import subprocess
import tempfile
from pathlib import Path
import time
import numpy as np
import torch
from scipy.io.wavfile import write as write_wav
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

class AudioGenerator:
    """Генерация аудио через XTTS с поддержкой фрагментов, пауз и субтитров"""
    def __init__(self, work_dir, speaker='Claribel Dervla', speed=1.0, 
                 output_format='mp3', speaker_wav=None, 
                 fragment_pause=0.2, initial_pause=0.0,
                 progress_callback=None, start_time=None,
                 generate_subtitles=True,
                 temperature=0.85,
                 repetition_penalty=2.0,
                 length_penalty=1.0,
                 top_k=50,
                 top_p=0.85,
                 num_beams=1,
                 gpt_cond_len=12,
                 sound_norm_refs=True,
                 use_finetuned_model=False,
                 finetuned_model_path=""):
        self.work_dir = Path(work_dir)
        self.fragments_dir = self.work_dir / "03_text_fragments"
        self.audio_dir = self.work_dir / "04_audio"
        self.subtitles_dir = self.work_dir / "05_subtitles"
        self.audio_dir.mkdir(exist_ok=True)
        self.subtitles_dir.mkdir(exist_ok=True)
        
        self.speaker = speaker
        self.speed = speed
        self.output_format = output_format.lower()
        self.speaker_wav = speaker_wav
        self.fragment_pause = fragment_pause
        self.initial_pause = initial_pause
        self.generate_subtitles = generate_subtitles
        
        self.temperature = temperature
        self.repetition_penalty = repetition_penalty
        self.length_penalty = length_penalty
        self.top_k = top_k
        self.top_p = top_p
        self.num_beams = num_beams
        self.gpt_cond_len = gpt_cond_len
        self.sound_norm_refs = sound_norm_refs
        
        self.use_finetuned_model = use_finetuned_model
        self.finetuned_model_path = finetuned_model_path
        self.tts_model = None  # Для дообученной модели
        self.tts = None        # Для стандартной модели
        
        self.progress_callback = progress_callback
        self.start_time = start_time or time.time()
        
        print(f"Загрузка XTTS модели...")
        if use_finetuned_model and finetuned_model_path:
            print(f"  Режим: ДООБУЧЕННАЯ МОДЕЛЬ")
            print(f"  Путь: {finetuned_model_path}")
        else:
            print(f"  Режим: СТАНДАРТНАЯ МОДЕЛЬ")
        print(f"  Голос: {speaker if not speaker_wav else 'Клонирование: ' + speaker_wav}")
        print(f"  Скорость: {speed}x")
        print(f"  Пауза между фрагментами: {fragment_pause} сек")
        print(f"  Пауза в начале: {initial_pause} сек")
        print(f"  Формат: {self.output_format.upper()}")
        print(f"  Субтитры: {'включены' if generate_subtitles else 'выключены'}")
        
        self._load_model()

    def _format_time(self, seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes > 0:
            return f"{minutes} минут {secs} секунд"
        return f"{secs} секунд"

    def _format_srt_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _update_progress(self, current, total):
        if self.progress_callback:
            elapsed = time.time() - self.start_time
            elapsed_str = self._format_time(elapsed)
            self.progress_callback(current, total, elapsed_str)

    def _load_model(self):
        """Загрузка XTTS модели (стандартной или дообученной)"""
        try:
            if self.use_finetuned_model and self.finetuned_model_path:
                # Загрузка дообученной модели через XttsConfig
                model_path = Path(self.finetuned_model_path)
                
                if not model_path.exists():
                    raise FileNotFoundError(f"Папка с моделью не найдена: {model_path}")
                
                config_file = model_path / "config.json"
                model_file = model_path / "model.pth"
                vocab_file = model_path / "vocab.json"
                speaker_file = model_path / "speakers_xtts.pth"
                
                if not config_file.exists():
                    raise FileNotFoundError(f"config.json не найден в {model_path}")
                if not model_file.exists():
                    raise FileNotFoundError(f"model.pth не найден в {model_path}")
                if not vocab_file.exists():
                    raise FileNotFoundError(f"vocab.json не найден в {model_path}")
                
                print(f"  Загрузка дообученной модели из: {model_path}")
                
                config = XttsConfig()
                config.load_json(str(config_file))
                
                self.tts_model = Xtts.init_from_config(config)
                self.tts_model.load_checkpoint(
                    config,
                    checkpoint_path=str(model_file),
                    vocab_path=str(vocab_file),
                    speaker_file_path=str(speaker_file) if speaker_file.exists() else None,
                    use_deepspeed=False
                )
                
                if torch.cuda.is_available():
                    self.tts_model.cuda()
                else:
                    self.tts_model.cpu()
                
                print("Дообученная модель загружена успешно")
                return
            
            # Стандартная модель
            print("  Загрузка стандартной модели XTTS-v2...")
            self.tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
            print("Стандартная модель загружена успешно")
            
            # Обновляем параметры стандартной модели
            if hasattr(self.tts, 'synthesizer') and hasattr(self.tts.synthesizer, 'tts_model'):
                model = self.tts.synthesizer.tts_model
                model.temperature = self.temperature
                model.repetition_penalty = self.repetition_penalty
                model.length_penalty = self.length_penalty
                model.top_k = self.top_k
                model.top_p = self.top_p
                model.num_beams = self.num_beams
                model.gpt_cond_len = self.gpt_cond_len 
                model.sound_norm_refs = self.sound_norm_refs
                print("Параметры синтеза применены к стандартной модели")
                
        except Exception as e:
            print(f"Ошибка загрузки XTTS: {e}")
            raise

    def _get_conditioning_latents(self, speaker_wav=None, speaker=None):
        """Получение conditioning latents для дообученной модели"""
        if self.tts_model is None:
            return None, None
        
        try:
            if speaker_wav and os.path.exists(speaker_wav):
                gpt_cond_latent, speaker_embedding = self.tts_model.get_conditioning_latents(
                    audio_path=speaker_wav,
                    gpt_cond_len=self.gpt_cond_len,
                    max_ref_length=30,
                    sound_norm_refs=self.sound_norm_refs
                )
                return gpt_cond_latent, speaker_embedding
            else:
                speaker_id = speaker if speaker else "Claribel Dervla"
                if hasattr(self.tts_model, 'speaker_manager') and self.tts_model.speaker_manager is not None:
                    speaker_embedding = self.tts_model.speaker_manager.speakers[speaker_id]
                    gpt_cond_latent = torch.zeros(1, 1, 1024)
                    return gpt_cond_latent, speaker_embedding
                else:
                    return None, None
        except Exception as e:
            print(f"  Предупреждение: не удалось получить conditioning latents: {e}")
            return None, None

    def _generate_fragment_standard(self, text):
        """Генерация через стандартную модель"""
        tts_params = {
            'text': text,
            'language': 'ru',
            'speed': self.speed,
            'temperature': self.temperature,
            'repetition_penalty': self.repetition_penalty,
            'length_penalty': self.length_penalty,
            'top_k': self.top_k,
            'top_p': self.top_p,
            'num_beams': self.num_beams,
            'gpt_cond_len': self.gpt_cond_len,
            'sound_norm_refs': self.sound_norm_refs
        }
        
        if self.speaker_wav and os.path.exists(self.speaker_wav):
            tts_params['speaker_wav'] = self.speaker_wav
        else:
            tts_params['speaker'] = self.speaker
        
        tts_params['file_path'] = None
        return self.tts.tts(**tts_params)

    def _generate_fragment_finetuned(self, text):
        """Генерация через дообученную модель"""
        if self.tts_model is None:
            raise RuntimeError("Дообученная модель не загружена")
        
        gpt_cond_latent, speaker_embedding = self._get_conditioning_latents(
            speaker_wav=self.speaker_wav,
            speaker=self.speaker
        )
        
        if gpt_cond_latent is None or speaker_embedding is None:
            gpt_cond_latent = torch.zeros(1, 1, 1024)
            speaker_embedding = torch.zeros(1, 512)
        
        result = self.tts_model.inference(
            text=text,
            language='ru',
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            temperature=self.temperature,
            length_penalty=self.length_penalty,
            repetition_penalty=self.repetition_penalty,
            top_k=self.top_k,
            top_p=self.top_p,
            num_beams=self.num_beams,
            speed=self.speed,
            enable_text_splitting=True
        )
        
        return result['wav']

    def _save_audio(self, audio_data, output_path, sample_rate=24000):
        if hasattr(audio_data, 'cpu'):
            audio_data = audio_data.cpu().numpy()
        
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        if self.output_format == 'wav':
            write_wav(str(output_path), sample_rate, audio_int16)
            return output_path
        
        if self.output_format == 'mp3':
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_wav = tmp.name
            
            try:
                write_wav(tmp_wav, sample_rate, audio_int16)
                mp3_path = output_path.with_suffix('.mp3')
                cmd = ['ffmpeg', '-y', '-i', tmp_wav, '-b:a', '192k', '-ar', str(sample_rate), str(mp3_path)]
                subprocess.run(cmd, capture_output=True, check=True)
                return mp3_path
            finally:
                if os.path.exists(tmp_wav):
                    os.unlink(tmp_wav)
        
        return output_path

    def _clean_text(self, text):
        text = text.replace('+', '')
        import unicodedata
        text = unicodedata.normalize('NFD', text)
        text = ''.join(ch for ch in text if not unicodedata.combining(ch))
        return text

    def _generate_fragment(self, text):
        if self.use_finetuned_model and self.tts_model is not None:
            return self._generate_fragment_finetuned(text)
        else:
            return self._generate_fragment_standard(text)

    def generate_single_file(self, filename: str, progress_callback=None):
        """
        Генерация аудио только для одного файла по его имени
        
        Args:
            filename: имя исходного файла (например, '003_Двадцать слов к монахам.txt')
            progress_callback: функция для обновления прогресса (filename, pct, chars_done, chars_total)
        
        Returns:
            tuple: (audio_path, subtitle_path) или (None, None) если не удалось
        """
        stem = Path(filename).stem
        
        # Пробуем разные варианты имени папки с фрагментами
        possible_folders = [
            self.fragments_dir / f"{stem}_replaced",           # вариант 1: имя_replaced
            self.fragments_dir / f"{stem}_extracted_replaced", # вариант 2: имя_extracted_replaced
            self.fragments_dir / stem,                          # вариант 3: просто имя
        ]
        
        fragment_folder = None
        for folder in possible_folders:
            if folder.exists():
                fragment_folder = folder
                print(f"  Найдена папка с фрагментами: {folder.name}")
                break
        
        if fragment_folder is None:
            print(f"Папка с фрагментами не найдена. Искали: {[f.name for f in possible_folders]}")
            return None, None
        
        fragment_files = sorted(fragment_folder.glob("fragment_*.txt"))
        
        if not fragment_files:
            print(f"Нет файлов фрагментов в {fragment_folder}")
            return None, None
        
        print(f"  Генерация аудио для {filename}, фрагментов: {len(fragment_files)}")
        
        # 🔹 ИЗМЕНЕНО: Считаем общее количество символов для прогресса
        total_chars = 0
        fragment_data = []
        for frag_file in fragment_files:
            with open(frag_file, 'r', encoding='utf-8') as f:
                text = f.read()
            if text.strip():
                fragment_data.append((frag_file, text))
                total_chars += len(text)
        
        if total_chars == 0:
            print(f"  Нет текста для генерации")
            return None, None
        
        chars_processed = 0
        audio_parts = []
        fragments_data = []
        sample_rate = 24000
        current_time = self.initial_pause
        pause_samples = int(sample_rate * self.fragment_pause)
        initial_pause_samples = int(sample_rate * self.initial_pause)
        
        if self.initial_pause > 0:
            audio_parts.append(torch.zeros(initial_pause_samples))
        
        for i, (frag_file, text) in enumerate(fragment_data, 1):
            if not text.strip():
                continue
            
            print(f"    Фрагмент {i}/{len(fragment_data)}")
            audio = self._generate_fragment(text)
            
            # 🔹 ИЗМЕНЕНО: Обновляем прогресс по символам
            chars_processed += len(text)
            if progress_callback and total_chars > 0:
                pct = int(chars_processed / total_chars * 100)
                progress_callback(filename, pct, chars_processed, total_chars)
            
            if isinstance(audio, np.ndarray):
                audio = torch.from_numpy(audio)
            elif isinstance(audio, list) and len(audio) > 0:
                audio = audio[0] if isinstance(audio[0], torch.Tensor) else torch.from_numpy(np.array(audio))
            
            duration = audio.shape[0] / sample_rate
            
            if self.generate_subtitles:
                fragments_data.append({
                    'index': len(fragments_data) + 1,
                    'start': current_time,
                    'end': current_time + duration,
                    'text': self._clean_text(text)
                })
            
            audio_parts.append(audio)
            current_time += duration
            
            if i < len(fragment_data) and self.fragment_pause > 0:
                audio_parts.append(torch.zeros(pause_samples))
                current_time += self.fragment_pause
        
        if not audio_parts:
            print(f"  Нет сгенерированных фрагментов")
            return None, None
        
        final_audio = torch.cat(audio_parts)
        
        extension = '.mp3' if self.output_format == 'mp3' else '.wav'
        output_file = self.audio_dir / f"{stem}{extension}"
        self._save_audio(final_audio, output_file, sample_rate)
        print(f"  Сохранено аудио: {output_file.name}")
        
        subtitle_file = None
        if self.generate_subtitles and fragments_data:
            srt_file = self.subtitles_dir / f"{stem}.srt"
            with open(srt_file, 'w', encoding='utf-8') as f:
                for frag in fragments_data:
                    start_str = self._format_srt_time(frag['start'])
                    end_str = self._format_srt_time(frag['end'])
                    f.write(f"{frag['index']}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{frag['text']}\n\n")
            subtitle_file = srt_file
            print(f"  Сохранены субтитры: {srt_file.name}")
        
        return output_file, subtitle_file

    def generate_all(self):
        """Генерация аудио для всех файлов (для обратной совместимости)"""
        if not self.fragments_dir.exists():
            print(f"Папка {self.fragments_dir} не найдена")
            return [], []
        
        fragment_folders = [d for d in self.fragments_dir.iterdir() if d.is_dir()]
        
        if not fragment_folders:
            print("Нет папок с фрагментами")
            return [], []
        
        results = []
        subtitles_results = []
        total_files = len(fragment_folders)
        
        for idx, folder in enumerate(fragment_folders, 1):
            folder_name = folder.name
            # Извлекаем имя файла из имени папки (убираем _replaced или _extracted_replaced)
            filename = folder_name.replace('_replaced', '').replace('_extracted', '')
            
            print(f"\n--- Обработка: {filename} ---")
            audio_file, subtitle_file = self.generate_single_file(filename)
            
            if audio_file:
                results.append(audio_file)
            if subtitle_file:
                subtitles_results.append(subtitle_file)
            
            self._update_progress(idx, total_files)
        
        return results, subtitles_results

    def get_audio_files(self):
        extension = '.mp3' if self.output_format == 'mp3' else '.wav'
        return list(self.audio_dir.glob(f"*{extension}"))

    def get_subtitle_files(self):
        return list(self.subtitles_dir.glob("*.srt"))