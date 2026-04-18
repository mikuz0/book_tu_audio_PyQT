import re
from pathlib import Path
import PyPDF2
from ebooklib import epub
from bs4 import BeautifulSoup

class TextExtractor:
    """Извлечение текста из различных форматов"""
    
    def __init__(self, work_dir):
        self.work_dir = Path(work_dir)
        self.source_dir = self.work_dir / "source"
        self.extracted_dir = self.work_dir / "01_extracted_text"
        self.extracted_dir.mkdir(exist_ok=True)
        
        # Создаём папку source, если её нет
        self.source_dir.mkdir(exist_ok=True)
    
    def extract_from_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_from_pdf(self, file_path):
        text = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Страница {page_num + 1} ---\n{page_text}"
        except Exception as e:
            print(f"Ошибка чтения PDF {file_path}: {e}")
        return text
    
    def extract_from_epub(self, file_path):
        text = ""
        try:
            book = epub.read_epub(file_path)
            for item in book.get_items():
                if item.get_type() == 9:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text += soup.get_text() + "\n"
        except Exception as e:
            print(f"Ошибка чтения EPUB {file_path}: {e}")
        return text
    
    def extract_from_fb2(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'xml')
            return soup.get_text()
        except Exception as e:
            print(f"Ошибка чтения FB2 {file_path}: {e}")
        return ""
    
    def extract(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        ext = file_path.suffix.lower()
        
        if ext == '.txt':
            text = self.extract_from_txt(file_path)
        elif ext == '.pdf':
            text = self.extract_from_pdf(file_path)
        elif ext == '.epub':
            text = self.extract_from_epub(file_path)
        elif ext == '.fb2':
            text = self.extract_from_fb2(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат: {ext}")
        
        if not text:
            raise ValueError(f"Не удалось извлечь текст из {file_path}")
        
        text = self._clean_text(text)
        
        output_file = self.extracted_dir / f"{file_path.stem}_extracted.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return output_file
    
    def _clean_text(self, text):
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def extract_all(self):
        """Извлечь текст из всех поддерживаемых файлов в папке source"""
        if not self.source_dir.exists():
            print(f"Папка {self.source_dir} не найдена")
            return []
        
        supported_ext = ['.txt', '.pdf', '.epub', '.fb2']
        processed = []
        
        for ext in supported_ext:
            for file_path in self.source_dir.glob(f"*{ext}"):
                if file_path.is_file():
                    try:
                        output = self.extract(file_path)
                        processed.append(output)
                        print(f"  {file_path.name} -> {output.name}")
                    except Exception as e:
                        print(f"  Ошибка обработки {file_path.name}: {e}")
        
        return processed