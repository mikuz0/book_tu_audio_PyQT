#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработка текста: исправление ударений и разбиение на фрагменты
"""
import re
from pathlib import Path
from core.stress_dict import StressDictionary

class TextProcessor:
    """Обработка текста: исправление ударений и разбиение на фрагменты"""
    def __init__(self, work_dir):
        self.work_dir = Path(work_dir)
        self.extracted_dir = self.work_dir / "01_extracted_text"
        self.replaced_dir = self.work_dir / "02_replaced_text"
        self.fragments_dir = self.work_dir / "03_text_fragments"
        
        self.replaced_dir.mkdir(exist_ok=True)
        self.fragments_dir.mkdir(exist_ok=True)
        
        self.stress_dict = StressDictionary(work_dir)

    def apply_replacements(self, text):
        """Применить исправления из словаря"""
        return self.stress_dict.apply(text)

    def convert_to_unicode(self, text):
        """Преобразовать + в Unicode ударения"""
        STRESS_MAP = {
            'а': 'а́', 'А': 'А́', 'е': 'е́', 'Е': 'Е́', 'ё': 'ё́', 'Ё': 'Ё́',
            'и': 'и́', 'И': 'И́', 'о': 'о́', 'О': 'О́', 'у': 'у́', 'У': 'У́',
            'ы': 'ы́', 'Ы': 'Ы́', 'э': 'э́', 'Э': 'Э́', 'ю': 'ю́', 'Ю': 'Ю́', 
            'я': 'я́', 'Я': 'Я́'
        }
        
        result = text
        result = re.sub(r'\+([аеёиоуыэюя])', 
                        lambda m: STRESS_MAP.get(m.group(1).lower(), m.group(1)),
                        result, flags=re.I)
        result = re.sub(r'([аеёиоуыэюя])\+([аеёиоуыэюя])',
                        lambda m: m.group(1) + STRESS_MAP.get(m.group(2).lower(), m.group(2)),
                        result, flags=re.I)
        result = re.sub(r'([аеёиоуыэюя])\+',
                        lambda m: STRESS_MAP.get(m.group(1).lower(), m.group(1)),
                        result, flags=re.I)
        
        result = result.replace('+', '')
        return result

    def normalize_spaces(self, text):
        """Нормализация пробелов в тексте"""
        if not text:
            return ""
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', text)
        text = re.sub(r'\s+\.', '.', text)
        text = re.sub(r'\s+,', ',', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\.\s*([а-яё])', lambda m: '. ' + m.group(1).upper(), text, flags=re.I)
        return text.strip()

    def find_original_segment(self, fragment, original_text):
        """Поиск фрагмента в исходном тексте"""
        if not fragment or not original_text:
            return None, -1, -1
        
        search_fragment = fragment.strip()
        search_fragment = re.sub(r'\s+', ' ', search_fragment)
        
        pos = original_text.find(search_fragment)
        if pos != -1:
            end_pos = pos + len(search_fragment)
            return original_text[pos:end_pos], pos, end_pos
        
        start_part = search_fragment[:50] if len(search_fragment) > 50 else search_fragment
        end_part = search_fragment[-50:] if len(search_fragment) > 50 else search_fragment
        
        start_pos = original_text.find(start_part)
        if start_pos == -1:
            return None, -1, -1
            
        end_pos = original_text.rfind(end_part)
        if end_pos == -1 or end_pos < start_pos:
            return None, -1, -1
            
        end_pos = end_pos + len(end_part)
        return original_text[start_pos:end_pos], start_pos, end_pos

    def fix_fragment_end(self, text, terminator="."):
        """Гарантированная подстановка терминатора. Вызывается СТРОГО ПОСЛЕДНИМ."""
        if not text:
            return terminator or ""
        
        text = text.rstrip()
        if not text:
            return terminator or ""
            
        last_char = text[-1]
        
        # Запятая/двоеточие/точка с запятой в конце -> меняем на точку
        if last_char in ';:,':
            text = text[:-1] + '.'
            
        # Если терминатор - пробел (один или два)
        if terminator == " ":
            return text + " "
        if terminator == "  ":
            return text + "  "
            
        # Если уже заканчивается на нужный терминатор
        if text.endswith(terminator):
            return text
            
        # Если терминатор не точка, а текст заканчивается на .!? -> заменяем последний знак
        if terminator != '.' and text[-1] in '.!?':
            text = text[:-1] + terminator
        else:
            # Во всех остальных случаях добавляем терминатор
            text = text + terminator
            
        return text

    def fix_fragment_start(self, text):
        """Правка начала фрагмента"""
        if not text:
            return ""
        
        text = text.lstrip(' .,;:')
        if text.startswith('...'):
            text = text[3:].lstrip()
        elif text.startswith('..'):
            text = text[2:].lstrip()
        elif text.startswith('.'):
            text = text[1:].lstrip()
            
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
            
        return text

    def restore_fragment(self, fragment, original_text, terminator="."):
        """Восстановление фрагмента по исходному тексту с гарантированным терминатором"""
        if not fragment:
            return ""
            
        original_segment, _, _ = self.find_original_segment(fragment, original_text)
        result = original_segment if original_segment else fragment
        
        # 🔹 СТРОГИЙ ПОРЯДОК ВЫЗОВОВ:
        # 1. Сначала нормализуем пробелы внутри текста
        result = self.normalize_spaces(result)
        # 2. Правим начало (убираем мусор, делаем первую букву заглавной)
        result = self.fix_fragment_start(result)
        # 3. В САМОМ КОНЦЕ гарантированно добавляем/заменяем терминатор
        result = self.fix_fragment_end(result, terminator)
        
        return result

    def split_text(self, text, original_text, min_length=150, max_length=250, 
                   primary_delimiters=".!? ", secondary_delimiters=":; ", terminator="."):
        """
        🔹 ОДНОПРОХОДНЫЙ АЛГОРИТМ с корректной обработкой второстепенных разделителей:
        1. Накапливаем текст до основного разделителя (.!?)
        2. Если длина < min_length → продолжаем накапливать
        3. Если длина > max_length → ищем второстепенный разделитель (:;) С КОНЦА буфера
           - Находим первый подходящий символ, при котором длина ≤ max_length
           - Отрезаем фрагмент, остаток оставляем в буфере
        4. Если длина в [min_length, max_length] → сохраняем, очищаем буфер
        5. Повторяем до конца текста
        """
        fragments = []
        buffer = ""
        pos = 0
        text_len = len(text)

        while pos < text_len:
            # Находим позицию ближайшего основного разделителя
            next_delim_idx = text_len
            for delim in primary_delimiters:
                idx = text.find(delim, pos)
                if idx != -1 and idx < next_delim_idx:
                    next_delim_idx = idx

            # Захватываем текст до разделителя включительно
            chunk_end = next_delim_idx + 1 if next_delim_idx < text_len else text_len
            buffer += text[pos:chunk_end]
            pos = chunk_end

            buf_len = len(buffer)
            
            if buf_len >= min_length:
                fragment_to_save = None
                
                if buf_len <= max_length:
                    # Идеальный случай: длина в допустимых пределах
                    fragment_to_save = buffer.strip()
                    buffer = ""
                else:
                    # Слишком длинный → ищем второстепенный разделитель С КОНЦА
                    split_idx = -1
                    
                    # 🔹 ИЩЕМ С КОНЦА БУФЕРА до тех пор, пока длина не станет ≤ max_length
                    for i in range(buf_len - 1, max_length - 1, -1):
                        if buffer[i] in secondary_delimiters:
                            # Проверяем, что после отсечения длина будет ≥ min_length
                            candidate_len = i + 1
                            if candidate_len >= min_length:
                                split_idx = i
                                break
                            # Если меньше min_length — продолжаем поиск дальше к началу
                    
                    if split_idx != -1:
                        # Нашли подходящий разделитель → отрезаем
                        fragment_to_save = buffer[:split_idx+1].strip()
                        buffer = buffer[split_idx+1:]
                    else:
                        # Не нашли второстепенный разделитель → ищем основной после min_length
                        found = False
                        for i in range(min_length, buf_len):
                            if buffer[i] in primary_delimiters:
                                fragment_to_save = buffer[:i+1].strip()
                                buffer = buffer[i+1:]
                                found = True
                                break
                        
                        if not found:
                            # Крайний случай: жестко режем на max_length
                            fragment_to_save = buffer[:max_length].strip()
                            buffer = buffer[max_length:]
                
                if fragment_to_save:
                    fragments.append(self.restore_fragment(fragment_to_save, original_text, terminator))

        # Сохраняем остаток текста (хвост)
        if buffer.strip():
            fragments.append(self.restore_fragment(buffer.strip(), original_text, terminator))

        return fragments

    def process_file(self, input_file):
        """Применить словарь ударений и сохранить"""
        input_file = Path(input_file)
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
            
        if not text.strip():
            return None
            
        text = self.apply_replacements(text)
        text = self.convert_to_unicode(text)
        
        output_file = self.replaced_dir / f"{input_file.stem}_replaced.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
            
        return output_file

    def process_all(self):
        if not self.extracted_dir.exists():
            print(f"Папка {self.extracted_dir} не найдена")
            return []
            
        files = list(self.extracted_dir.glob("*.txt"))
        print(f"Найдено файлов: {len(files)}")
        
        results = []
        for f in files:
            print(f"\n--- {f.name} ---")
            try:
                result = self.process_file(f)
                if result:
                    results.append(result)
                    print(f"  Сохранено: {result.name}")
            except Exception as e:
                print(f"  ОШИБКА: {e}")
                
        return results

    def split_file(self, input_file, original_text, min_length=150, max_length=250,
                   primary_delimiters=".!? ", secondary_delimiters=":; ", terminator="."):
        """Разбить файл на фрагменты и сохранить"""
        input_file = Path(input_file)
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
            
        if not text.strip():
            return []
            
        fragments = self.split_text(text, original_text, min_length, max_length, 
                                     primary_delimiters, secondary_delimiters, terminator)
        
        output_dir = self.fragments_dir / input_file.stem
        output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        for i, frag in enumerate(fragments, 1):
            frag_file = output_dir / f"fragment_{i:03d}.txt"
            with open(frag_file, 'w', encoding='utf-8') as f:
                f.write(frag)
            saved_files.append(frag_file)
            
        return saved_files

    def split_all(self, min_length=150, max_length=250,
                  primary_delimiters=".!? ", secondary_delimiters=":; ", terminator="."):
        if not self.replaced_dir.exists():
            print(f"Папка {self.replaced_dir} не найдена")
            return {}
            
        files = list(self.replaced_dir.glob("*_replaced.txt"))
        print(f"Найдено файлов: {len(files)}")
        
        results = {}
        for f in files:
            print(f"\n--- {f.name} ---")
            try:
                base_name = f.stem.replace('_replaced', '')
                extracted_file = self.extracted_dir / f"{base_name}_extracted.txt"
                
                original_text = None
                if extracted_file.exists():
                    with open(extracted_file, 'r', encoding='utf-8') as ef:
                        original_text = ef.read()
                else:
                    print(f"  Предупреждение: не найден оригинальный файл {extracted_file}")
                    
                fragments = self.split_file(f, original_text, min_length, max_length,
                                            primary_delimiters, secondary_delimiters, terminator)
                results[f.name] = fragments
                print(f"  Разбито на {len(fragments)} фрагментов")
                if fragments:
                    valid_lengths = [len(frag) for frag in fragments if isinstance(frag, str)]
                    if valid_lengths:
                        print(f"  Длина: мин={min(valid_lengths)}, макс={max(valid_lengths)}")
            except Exception as e:
                print(f"  ОШИБКА: {e}")
                
        return results