#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вкладка логов выполнения
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit
from PyQt5.QtGui import QFont


class LogTab(QWidget):
    """Вкладка с логами выполнения"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Очистить лог")
        clear_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def append_log(self, message: str):
        """Добавить сообщение в лог"""
        self.log_text.append(message)
    
    def clear_log(self):
        """Очистить лог"""
        self.log_text.clear()