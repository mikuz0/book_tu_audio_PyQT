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
        # .strip() допустим только ДО применения терминатора
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
        
        # Fallback поиск по началам и концам
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
        """🔹 Гарантированная подстановка терминатора. Вызывается СТРОГО ПОСЛЕДНИМ."""
        if not text:
            return terminator or ""
        
        text = text.rstrip()
        if not text:
            return terminator or ""
            
        last_char = text[-1]
        
        # Запятая/двоеточие/точка с запятой в конце -> меняем на точку
        if last_char in ';:,':
            text = text[:-1] + '.'
            
        # Если терминатор - пробел
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
        
        # Убираем мусор в начале
        text = text.lstrip(' .,;:')
        if text.startswith('...'):
            text = text[3:].lstrip()
        elif text.startswith('..'):
            text = text[2:].lstrip()
        elif text.startswith('.'):
            text = text[1:].lstrip()
            
        # Первая буква заглавная
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
            
        return text

    def restore_fragment(self, fragment, original_text, terminator="."):
        """🔹 ИСПРАВЛЕНО: строгий порядок вызовов"""
        if not fragment:
            return ""
            
        original_segment, _, _ = self.find_original_segment(fragment, original_text)
        result = original_segment if original_segment else fragment
        
        # 1. Нормализуем пробелы
        result = self.normalize_spaces(result)
        # 2. Правим начало (убираем мусор, делаем первую букву заглавной)
        result = self.fix_fragment_start(result)
        # 3. В САМОМ КОНЦЕ гарантированно добавляем/заменяем терминатор
        result = self.fix_fragment_end(result, terminator)
        
        return result

    def merge_short_fragments(self, fragments, min_length):
        """Объединение коротких фрагментов"""
        if not fragments:
            return []
            
        merged = []
        buffer = ""
        
        for frag in fragments:
            if buffer:
                buffer += " " + frag
            else:
                buffer = frag
                
            if len(buffer) >= min_length:
                merged.append(buffer.strip())
                buffer = ""
                
        # 🔹 Обработка остатка: если он короче min_length, приклеиваем к последнему
        if buffer:
            if merged and len(buffer) < min_length:
                merged[-1] = merged[-1] + " " + buffer
            else:
                merged.append(buffer.strip())
                
        return merged

    def split_by_delimiters(self, text, delimiters):
        """Разбиение текста по указанным символам"""
        parts = []
        current = ""
        
        for ch in text:
            current += ch
            if ch in delimiters:
                if current.strip():
                    parts.append(current.strip())
                current = ""
                
        if current.strip():
            parts.append(current.strip())
            
        return parts

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

    def split_text(self, text, original_text, min_length=150, max_length=250, 
                   primary_delimiters=".!? ", secondary_delimiters=":; ", terminator="."):
        """🔹 ИСПРАВЛЕНО: убрано жёсткое разбиение, исправлена логика склейки"""
        # Шаг 1: Разбиение по главным разделителям
        parts = self.split_by_delimiters(text, primary_delimiters)
        
        # Шаг 2: Объединение коротких (1-й проход)
        merged = self.merge_short_fragments(parts, min_length)
        
        # Шаг 3: Разбиение длинных по второстепенным разделителям
        final_parts = []
        for part in merged:
            if len(part) <= max_length:
                final_parts.append(part)
            else:
                sub_parts = self.split_by_delimiters(part, secondary_delimiters)
                # 🔹 Если второстепенные разделители сработали -> используем их
                # 🔹 ИНАЧЕ оставляем длинный фрагмент как есть (жёсткий split УБРАН)
                final_parts.extend(sub_parts if len(sub_parts) > 1 else [part])
                
        # Шаг 4: Объединение коротких (2-й проход)
        merged_again = self.merge_short_fragments(final_parts, min_length)
        
        # Шаг 5: Восстановление по исходному тексту и применение терминатора
        restored_parts = []
        for part in merged_again:
            restored = self.restore_fragment(part, original_text, terminator)
            if restored:  # Сохраняем только непустые результаты
                restored_parts.append(restored)
                
        return restored_parts

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