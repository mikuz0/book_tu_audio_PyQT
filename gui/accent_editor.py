#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Редактор JSON-файла с ударениями (символ +)
"""

import sys
import json
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QFileDialog, QMessageBox,
    QLineEdit, QLabel, QHeaderView, QStatusBar, QShortcut,
    QMenuBar, QMenu, QAction, QInputDialog, QCheckBox, QSplitter
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QKeySequence


class AccentEditorWindow(QMainWindow):
    """Главное окно редактора файлов с ударениями"""
    
    def __init__(self, file_path=None):
        super().__init__()
        self.current_file: Optional[Path] = None
        self.data: Dict[str, str] = {}
        self.modified = False
        self.settings = QSettings('AccentEditor', 'Editor')
        
        self.init_ui()
        
        if file_path:
            self.load_data(Path(file_path))
        else:
            self.load_last_path()
        
        self.update_status_bar()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Редактор ударений (JSON)")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Панель инструментов
        toolbar_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("📂 Открыть")
        self.btn_open.clicked.connect(self.open_file)
        toolbar_layout.addWidget(self.btn_open)
        
        self.btn_save = QPushButton("💾 Сохранить")
        self.btn_save.clicked.connect(self.save_file)
        toolbar_layout.addWidget(self.btn_save)
        
        self.btn_save_as = QPushButton("📄 Сохранить как...")
        self.btn_save_as.clicked.connect(self.save_file_as)
        toolbar_layout.addWidget(self.btn_save_as)
        
        toolbar_layout.addStretch()
        
        self.btn_add = QPushButton("➕ Добавить запись")
        self.btn_add.clicked.connect(self.add_entry)
        toolbar_layout.addWidget(self.btn_add)
        
        self.btn_delete = QPushButton("🗑 Удалить запись")
        self.btn_delete.clicked.connect(self.delete_entry)
        toolbar_layout.addWidget(self.btn_delete)
        
        main_layout.addLayout(toolbar_layout)
        
        # Панель поиска
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по ключу или значению...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        
        self.case_sensitive = QCheckBox("Учитывать регистр")
        search_layout.addWidget(self.case_sensitive)
        search_layout.addStretch()
        
        main_layout.addLayout(search_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Ключ", "Значение (с +)", "Предпросмотр (без +)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)
        
        # Строка состояния
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel()
        self.status_bar.addWidget(self.status_label)
        
        # Горячие клавиши
        QShortcut(QKeySequence.Save, self).activated.connect(self.save_file)
        QShortcut(QKeySequence.Open, self).activated.connect(self.open_file)
        QShortcut(QKeySequence.Delete, self).activated.connect(self.delete_entry)
        QShortcut("Ctrl+N", self).activated.connect(self.add_entry)
        
        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        
        open_action = QAction("Открыть", self)
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut(QKeySequence.Open)
        file_menu.addAction(open_action)
        
        save_action = QAction("Сохранить", self)
        save_action.triggered.connect(self.save_file)
        save_action.setShortcut(QKeySequence.Save)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Сохранить как...", self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut(QKeySequence.Quit)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("Правка")
        
        add_action = QAction("Добавить запись", self)
        add_action.triggered.connect(self.add_entry)
        add_action.setShortcut("Ctrl+N")
        edit_menu.addAction(add_action)
        
        delete_action = QAction("Удалить запись", self)
        delete_action.triggered.connect(self.delete_entry)
        delete_action.setShortcut(QKeySequence.Delete)
        edit_menu.addAction(delete_action)
    
    def load_last_path(self):
        last_path = self.settings.value('last_path', '')
        if last_path:
            self.last_path = last_path
        else:
            self.last_path = str(Path.home())
    
    def save_last_path(self):
        if self.current_file:
            self.settings.setValue('last_path', str(self.current_file.parent))
        elif hasattr(self, 'last_path'):
            self.settings.setValue('last_path', self.last_path)
    
    def update_status_bar(self):
        if self.current_file:
            file_info = f"Файл: {self.current_file.name}"
        else:
            file_info = "Файл не открыт"
        
        modified_mark = " *" if self.modified else ""
        entries_count = f" | Записей: {len(self.data)}"
        self.status_label.setText(f"{file_info}{modified_mark}{entries_count}")
    
    def set_modified(self, modified: bool):
        self.modified = modified
        self.update_status_bar()
        self.setWindowModified(modified)
    
    def load_data(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.current_file = file_path
            self.set_modified(False)
            self.update_table()
            self.save_last_path()
            
            self.status_bar.showMessage(f"Загружено {len(self.data)} записей", 3000)
            self.setWindowTitle(f"Редактор ударений - {file_path.name}")
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Ошибка", f"Неверный формат JSON:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{e}")
    
    def save_data(self, file_path: Path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            self.current_file = file_path
            self.set_modified(False)
            self.save_last_path()
            
            self.status_bar.showMessage(f"Сохранено в {file_path.name}", 3000)
            self.setWindowTitle(f"Редактор ударений - {file_path.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")
    
    def open_file(self):
        if self.modified:
            reply = QMessageBox.question(
                self, "Несохраненные изменения",
                "Имеются несохраненные изменения. Сохранить перед открытием?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                if not self.save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", self.last_path,
            "JSON файлы (*.json);;Все файлы (*.*)"
        )
        
        if file_path:
            self.load_data(Path(file_path))
    
    def save_file(self) -> bool:
        if not self.current_file:
            return self.save_file_as()
        else:
            self.save_data(self.current_file)
            return True
    
    def save_file_as(self) -> bool:
        if self.current_file:
            initial_path = self.current_file.parent / f"{self.current_file.stem}_new.json"
        else:
            initial_path = Path(self.last_path) / "accents.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл", str(initial_path),
            "JSON файлы (*.json);;Все файлы (*.*)"
        )
        
        if file_path:
            self.save_data(Path(file_path))
            return True
        return False
    
    def update_table(self):
        self.table.blockSignals(True)
        
        search_text = self.search_input.text()
        filtered_data = self.filter_data(search_text)
        
        self.table.setRowCount(len(filtered_data))
        self.table.setUpdatesEnabled(False)
        
        for row, (key, value) in enumerate(filtered_data.items()):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, key_item)
            
            value_item = QTableWidgetItem(value)
            self.table.setItem(row, 1, value_item)
            
            preview = value.replace('+', '')
            preview_item = QTableWidgetItem(preview)
            preview_item.setFlags(preview_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, preview_item)
        
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
    
    def filter_data(self, search_text: str) -> Dict[str, str]:
        if not search_text:
            return self.data
        
        filtered = {}
        case_sensitive = self.case_sensitive.isChecked()
        
        for key, value in self.data.items():
            if not case_sensitive:
                search_lower = search_text.lower()
                if search_lower in key.lower() or search_lower in value.lower():
                    filtered[key] = value
            else:
                if search_text in key or search_text in value:
                    filtered[key] = value
        
        return filtered
    
    def filter_table(self):
        self.update_table()
    
    def on_item_changed(self, item):
        if item.column() != 1:
            return
        
        row = item.row()
        key_item = self.table.item(row, 0)
        if not key_item:
            return
        
        key = key_item.text()
        new_value = item.text()
        
        filtered = self.filter_data(self.search_input.text())
        filtered_keys = list(filtered.keys())
        
        if row < len(filtered_keys):
            original_key = filtered_keys[row]
            if original_key in self.data and self.data[original_key] != new_value:
                self.data[original_key] = new_value
                self.set_modified(True)
                
                preview_item = self.table.item(row, 2)
                if preview_item:
                    preview_item.setText(new_value.replace('+', ''))
    
    def add_entry(self):
        key, ok = QInputDialog.getText(
            self, "Добавить запись", "Введите ключ (слово или фразу):"
        )
        
        if ok and key:
            if key in self.data:
                QMessageBox.warning(self, "Ошибка", f"Ключ '{key}' уже существует")
                return
            
            value, ok = QInputDialog.getText(
                self, "Добавить запись", f"Введите значение для ключа '{key}':"
            )
            
            if ok:
                self.data[key] = value
                self.set_modified(True)
                self.update_table()
                self.status_bar.showMessage(f"Добавлена запись: {key}", 2000)
    
    def delete_entry(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Информация", "Выберите запись для удаления")
            return
        
        filtered = self.filter_data(self.search_input.text())
        filtered_keys = list(filtered.keys())
        
        if current_row < len(filtered_keys):
            key = filtered_keys[current_row]
            
            reply = QMessageBox.question(
                self, "Подтверждение", f"Удалить запись '{key}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.data[key]
                self.set_modified(True)
                self.update_table()
                self.status_bar.showMessage(f"Удалена запись: {key}", 2000)
    
    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(
                self, "Несохраненные изменения",
                "Имеются несохраненные изменения. Сохранить перед выходом?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                if not self.save_file():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        self.save_last_path()
        event.accept()