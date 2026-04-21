#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация аудио через XTTS с корректным разделением параметров для стандартной и дообученной моделей
"""
import os
import re
import subprocess
import tempfile
import unicodedata
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
                 temperature=0.85, repetition_penalty=2.0, length_penalty=1.0,
                 top_k=50, top_p=0.85, num_beams=1,
                 gpt_cond_len=12, sound_norm_refs=True,
                 use_finetuned_model=False, finetuned_model_path=""):
        
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
        
        # Параметры синтеза (общие)
        self.temperature = temperature
        self.repetition_penalty = repetition_penalty
        self.length_penalty = length_penalty
        self.top_k = top_k
        self.top_p = top_p
        self.num_beams = num_beams
        
        # Параметры, специфичные для подготовки латентов (НЕ для inference!)
        self.gpt_cond_len = gpt_cond_len
        self.sound_norm_refs = sound_norm_refs
        
        self.use_finetuned_model = use_finetuned_model
        self.finetuned_model_path = finetuned_model_path
        self.tts_model = None  # Для дообученной модели
        self.tts = None        # Для стандартной модели
        
        self.progress_callback = progress_callback
        self.start_time = start_time or time.time()
        
        print("Загрузка XTTS модели...")
        if use_finetuned_model and finetuned_model_path:
            print(f"  Режим: ДООБУЧЕННАЯ МОДЕЛЬ")
            print(f"  Путь: {finetuned_model_path}")
        else:
            print("  Режим: СТАНДАРТНАЯ МОДЕЛЬ")
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
        return f"{minutes} мин {secs} сек" if minutes > 0 else f"{secs} сек"

    def _format_srt_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _update_progress(self, current, total):
        if self.progress_callback:
            elapsed = time.time() - self.start_time
            self.progress_callback(current, total, self._format_time(elapsed))

    def _load_model(self):
        """Загрузка XTTS модели (стандартной или дообученной)"""
        try:
            if self.use_finetuned_model and self.finetuned_model_path:
                # === ДОБУЧЕННАЯ МОДЕЛЬ ===
                model_path = Path(self.finetuned_model_path)
                if not model_path.exists():
                    raise FileNotFoundError(f"Папка с моделью не найдена: {model_path}")
                
                config_file = model_path / "config.json"
                model_file = model_path / "model.pth"
                vocab_file = model_path / "vocab.json"
                speaker_file = model_path / "speakers_xtts.pth"
                
                for f, name in [(config_file, "config.json"), (model_file, "model.pth"), (vocab_file, "vocab.json")]:
                    if not f.exists():
                        raise FileNotFoundError(f"Отсутствует обязательный файл: {name}")
                
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
                print("✅ Дообученная модель загружена")
                return
            
            # === СТАНДАРТНАЯ МОДЕЛЬ ===
            print("  Загрузка стандартной модели XTTS-v2...")
            self.tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=torch.cuda.is_available())
            print("✅ Стандартная модель загружена")
            
            # 🔹 Параметры применяются НАПРЯМУЮ на модель, а не передаются в tts()
            if hasattr(self.tts, 'synthesizer') and hasattr(self.tts.synthesizer, 'tts_model'):
                m = self.tts.synthesizer.tts_model
                m.temperature = self.temperature
                m.repetition_penalty = self.repetition_penalty
                m.length_penalty = self.length_penalty
                m.top_k = self.top_k
                m.top_p = self.top_p
                m.num_beams = self.num_beams
                # 🔹 Эти параметры ТОЛЬКО на модель, НЕ в tts()
                m.gpt_cond_len = self.gpt_cond_len
                m.sound_norm_refs = self.sound_norm_refs
                
        except Exception as e:
            print(f"❌ Ошибка загрузки XTTS: {e}")
            raise

    def _get_conditioning_latents(self, speaker_wav=None, speaker=None):
        """Получение conditioning latents для дообученной модели"""
        if self.tts_model is None:
            return None, None
        try:
            if speaker_wav and os.path.exists(speaker_wav):
                # 🔹 Здесь передаём gpt_cond_len и sound_norm_refs — это корректно!
                return self.tts_model.get_conditioning_latents(
                    audio_path=speaker_wav,
                    gpt_cond_len=self.gpt_cond_len,
                    max_ref_length=30,
                    sound_norm_refs=self.sound_norm_refs
                )
            else:
                speaker_id = speaker or "Claribel Dervla"
                if hasattr(self.tts_model, 'speaker_manager') and self.tts_model.speaker_manager:
                    emb = self.tts_model.speaker_manager.speakers.get(speaker_id)
                    if emb is not None:
                        return torch.zeros(1, 1, 1024), emb
                return None, None
        except Exception as e:
            print(f"⚠️ Не удалось получить conditioning latents: {e}")
            return None, None

    def _prepare_text_for_tts(self, text: str) -> str:
        """Нормализация текста перед подачей в XTTS"""
        if not text:
            return ""
        text = unicodedata.normalize('NFC', text)
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\n\r\t')
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        return text

    def _generate_fragment_standard(self, text: str) -> torch.Tensor:
        """🔹 Генерация через СТАНДАРТНУЮ модель — только валидные параметры для tts()"""
        # Параметры, которые МОЖНО передавать в tts() стандартной модели:
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
            'split_sentences': False,  # 🔹 Отключаем внутренний сплит!
            'file_path': None
        }
        
        # 🔹 Логика голоса: приоритет speaker_wav, но с фоллбэком на speaker
        if self.speaker_wav and os.path.exists(self.speaker_wav):
            tts_params['speaker_wav'] = self.speaker_wav
            tts_params['speaker'] = self.speaker  # Фоллбэк для совместимости
        elif self.speaker:
            tts_params['speaker'] = self.speaker
        
        return self.tts.tts(**tts_params)

    def _generate_fragment_finetuned(self, text: str) -> torch.Tensor:
        """🔹 Генерация через ДОБУЧЕННУЮ модель — параметры передаются в inference()"""
        if self.tts_model is None:
            raise RuntimeError("Дообученная модель не загружена")
        
        # 🔹 Получаем латенты с корректными параметрами (gpt_cond_len, sound_norm_refs)
        gpt_cond_latent, speaker_embedding = self._get_conditioning_latents(
            speaker_wav=self.speaker_wav,
            speaker=self.speaker
        )
        if gpt_cond_latent is None or speaker_embedding is None:
            gpt_cond_latent = torch.zeros(1, 1, 1024)
            speaker_embedding = torch.zeros(1, 512)
        
        # 🔹 В inference() передаём ТОЛЬКО параметры декодирования
        # ❌ НЕ передаём: gpt_cond_len, sound_norm_refs — они уже учтены в латентах!
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
            enable_text_splitting=False  # 🔹 Отключаем внутренний сплит для предразбитых фрагментов!
        )
        return result['wav']

    def _generate_fragment(self, text: str) -> torch.Tensor:
        """Единая точка входа для генерации фрагмента"""
        clean_text = self._prepare_text_for_tts(text)
        if self.use_finetuned_model and self.tts_model is not None:
            return self._generate_fragment_finetuned(clean_text)
        return self._generate_fragment_standard(clean_text)

    def _save_audio(self, audio_data, output_path, sample_rate=24000) -> Path:
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
                cmd = ['ffmpeg', '-y', '-i', tmp_wav, '-b:a', '192k', '-ar', str(sample_rate), str(output_path)]
                subprocess.run(cmd, capture_output=True, check=True, timeout=30)
                return output_path
            finally:
                if os.path.exists(tmp_wav):
                    os.unlink(tmp_wav)
        return output_path

    def _clean_text(self, text: str) -> str:
        text = text.replace('+', '')
        text = unicodedata.normalize('NFD', text)
        return ''.join(ch for ch in text if not unicodedata.combining(ch))

    def _generate_detailed_srt_segments(self, fragment_text: str, frag_start: float, frag_end: float) -> list:
        parts = re.split(r'([.!?]+)', fragment_text)
        sentences = []
        for i in range(0, len(parts), 2):
            sent_text = parts[i].strip()
            punct = parts[i+1] if i+1 < len(parts) else ''
            if sent_text:
                sentences.append(sent_text + punct)
            elif punct and sentences:
                sentences[-1] += punct
                
        if not sentences:
            return [{'start': frag_start, 'end': frag_end, 'text': self._clean_text(fragment_text.strip())}]
            
        total_chars = sum(len(s) for s in sentences)
        if total_chars == 0:
            return [{'start': frag_start, 'end': frag_end, 'text': self._clean_text(fragment_text.strip())}]
            
        detailed = []
        current_time = frag_start
        frag_duration = frag_end - frag_start
        
        for idx, sent in enumerate(sentences):
            sent_ratio = len(sent) / total_chars
            end_time = frag_end if idx == len(sentences) - 1 else current_time + frag_duration * sent_ratio
            detailed.append({
                'start': current_time, 'end': end_time,
                'text': self._clean_text(sent)
            })
            current_time = end_time
        return detailed

    def generate_single_file(self, filename: str, progress_callback=None) -> tuple:
        cb = progress_callback or self.progress_callback
        stem = Path(filename).stem
        
        possible_folders = [
            self.fragments_dir / f"{stem}_replaced",
            self.fragments_dir / f"{stem}_extracted_replaced",
            self.fragments_dir / stem,
        ]
        fragment_folder = next((f for f in possible_folders if f.exists()), None)
        if not fragment_folder:
            print(f"❌ Папка с фрагментами не найдена.")
            return None, None
            
        fragment_files = sorted(fragment_folder.glob("fragment_*.txt"))
        if not fragment_files:
            print(f"❌ Нет файлов фрагментов.")
            return None, None
            
        print(f"  Генерация: {filename} ({len(fragment_files)} фрагментов)")
        
        total_chars = sum(len(Path(f).read_text(encoding='utf-8').strip()) for f in fragment_files)
        chars_processed = 0
        audio_parts = []
        fragments_srt_data = []
        sample_rate = 24000
        current_time = self.initial_pause
        pause_samples = int(sample_rate * self.fragment_pause)
        
        if self.initial_pause > 0:
            audio_parts.append(torch.zeros(int(sample_rate * self.initial_pause)))
            
        for i, frag_file in enumerate(fragment_files, 1):
            text = frag_file.read_text(encoding='utf-8')
            if not text.strip(): continue
            
            print(f"    [{i}/{len(fragment_files)}] ", end="", flush=True)
            audio = self._generate_fragment(text)
            chars_processed += len(text)
            if cb and total_chars > 0:
                cb(filename, int(chars_processed/total_chars*100), chars_processed, total_chars)
                
            if isinstance(audio, np.ndarray): audio = torch.from_numpy(audio)
            elif isinstance(audio, list) and len(audio) > 0:
                audio = audio[0] if isinstance(audio[0], torch.Tensor) else torch.from_numpy(np.array(audio))
                
            duration = audio.shape[0] / sample_rate
            if self.generate_subtitles:
                fragments_srt_data.extend(self._generate_detailed_srt_segments(text, current_time, current_time + duration))
                
            audio_parts.append(audio)
            current_time += duration
            if i < len(fragment_files) and self.fragment_pause > 0:
                audio_parts.append(torch.zeros(pause_samples))
                current_time += self.fragment_pause
                
        if not audio_parts: return None, None
        
        final_audio = torch.cat(audio_parts)
        ext = '.mp3' if self.output_format == 'mp3' else '.wav'
        out_file = self.audio_dir / f"{stem}{ext}"
        self._save_audio(final_audio, out_file, sample_rate)
        print(f"✅ Сохранено аудио: {out_file.name}")
        
        sub_file = None
        if self.generate_subtitles and fragments_srt_data:
            srt_path = self.subtitles_dir / f"{stem}.srt"
            with open(srt_path, 'w', encoding='utf-8') as f:
                for idx, seg in enumerate(fragments_srt_data, 1):
                    f.write(f"{idx}\n{self._format_srt_time(seg['start'])} --> {self._format_srt_time(seg['end'])}\n{seg['text']}\n\n")
            sub_file = srt_path
            print(f"✅ Сохранены субтитры: {srt_path.name}")
        return out_file, sub_file

    def generate_all(self):
        if not self.fragments_dir.exists(): return [], []
        results, subs = [], []
        for idx, d in enumerate([p for p in self.fragments_dir.iterdir() if p.is_dir()], 1):
            name = d.name.replace('_replaced', '').replace('_extracted', '')
            a, s = self.generate_single_file(name)
            if a: results.append(a)
            if s: subs.append(s)
            self._update_progress(idx, len([p for p in self.fragments_dir.iterdir() if p.is_dir()]))
        return results, subs

    def get_audio_files(self):
        return list(self.audio_dir.glob(f"*.{self.output_format}"))
    
    def get_subtitle_files(self):
        return list(self.subtitles_dir.glob("*.srt"))