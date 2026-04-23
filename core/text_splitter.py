#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Адаптер для RecursiveCharacterTextSplitter из LangChain
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional


class TextSplitter:
    """Адаптер для рекурсивного разбиения текста"""
    
    DEFAULT_SEPARATORS = [
        "\n\n",     # Абзацы
        "\n",       # Строки
        ". ",       # Предложения (точка с пробелом)
        "! ",       # Восклицание
        "? ",       # Вопрос
        ".", "!", "?",  # Знаки без пробела
        ", ",       # Запятая с пробелом
        ",",        # Запятая
        "; ",       # Точка с запятой
        ";",
        ": ",       # Двоеточие
        ":",
        " ",        # Пробел
        ""          # Символы (крайний случай)
    ]
    
    def __init__(
        self,
        chunk_size: int = 250,
        chunk_overlap: int = 0,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS
        self._create_splitter()
    
    def _create_splitter(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            keep_separator=True,
            is_separator_regex=False
        )
    
    def _postprocess(self, fragments: List[str]) -> List[str]:
        """
        Постобработка фрагментов:
        1. Переносим разделитель из начала фрагмента в конец предыдущего
        2. Удаляем лишние пробелы в начале
        3. Удаляем пустые фрагменты
        """
        if not fragments:
            return []
        
        result = []
        
        for frag in fragments:
            # Удаляем лишние пробелы в начале
            frag = frag.lstrip()
            
            if not frag:
                continue
            
            # Если фрагмент начинается с разделителя и есть предыдущий фрагмент
            if frag and frag[0] in '.!?,;:' and result:
                # Берём разделитель
                separator = frag[0]
                # Остаток текста после разделителя
                rest = frag[1:].lstrip()
                
                # Добавляем разделитель к предыдущему фрагменту
                result[-1] = result[-1] + separator
                
                # Если остаток не пустой, добавляем его как следующий фрагмент
                if rest:
                    result.append(rest)
                # Если остаток пустой, ничего не добавляем
            else:
                # Обычный фрагмент
                result.append(frag)
        
        return result
    
    def split_text(self, text: str) -> List[str]:
        """Разбить текст на фрагменты"""
        if not text or not text.strip():
            return []
        
        fragments = self.splitter.split_text(text)
        fragments = self._postprocess(fragments)
        
        # Удаляем пустые фрагменты
        cleaned = [f for f in fragments if f.strip()]
        
        return cleaned
    
    def update_params(self, chunk_size: int = None, chunk_overlap: int = None):
        if chunk_size is not None:
            self.chunk_size = chunk_size
        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap
        self._create_splitter()