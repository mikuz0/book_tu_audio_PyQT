#!/bin/bash
# =============================================================================
# Скрипт установки рабочего окружения для программы "Книги в аудио"
# Версия: 1.1
# Описание: Устанавливает Python 3.11.9, создаёт виртуальное окружение,
#           устанавливает все зависимости для работы XTTS и GUI.
#           Исправлена проблема с transformers (BeamSearchScorer)
# =============================================================================

set -e  # Останавливаем скрипт при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
PYTHON_VERSION="3.11.9"
PYTHON_SRC_DIR="python_src"
VENV_DIR="xtts_env"
LOG_FILE="install.log"
REQUIREMENTS_FILE="requirements.txt"

# =============================================================================
# Функции
# =============================================================================

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

print_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║               Установка окружения для Книги в аудио              ║"
    echo "║                     Версия: XTTS + субтитры                       ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
}

check_system_dependencies() {
    log "Проверка системных зависимостей..."
    
    local missing_packages=()
    
    # Список необходимых пакетов для Ubuntu/Debian
    local required_packages=(
        "build-essential"
        "gcc"
        "g++"
        "make"
        "libssl-dev"
        "zlib1g-dev"
        "libbz2-dev"
        "libreadline-dev"
        "libsqlite3-dev"
        "libncurses5-dev"
        "libgdbm-dev"
        "libdb5.3-dev"
        "libexpat1-dev"
        "liblzma-dev"
        "tk-dev"
        "libffi-dev"
        "wget"
        "curl"
        "git"
        "ffmpeg"
    )
    
    for pkg in "${required_packages[@]}"; do
        if ! dpkg -l | grep -q "^ii.*$pkg"; then
            missing_packages+=("$pkg")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        log_warning "Отсутствуют следующие пакеты: ${missing_packages[*]}"
        echo ""
        echo "Выполните команду для установки:"
        echo "  sudo apt update"
        echo "  sudo apt install -y ${missing_packages[*]}"
        echo ""
        read -p "Нажмите Enter после установки пакетов, или Ctrl+C для выхода..."
    fi
    
    # Проверяем ffmpeg отдельно
    if ! command -v ffmpeg &> /dev/null; then
        log_warning "FFmpeg не установлен. Установите его: sudo apt install ffmpeg"
    fi
    
    log_success "Проверка системных зависимостей завершена"
}

download_and_build_python() {
    log "Скачивание и сборка Python $PYTHON_VERSION..."
    
    # Создаём директорию для исходников
    mkdir -p "$PYTHON_SRC_DIR"
    cd "$PYTHON_SRC_DIR"
    
    # Скачиваем Python если ещё не скачан
    if [ ! -f "Python-$PYTHON_VERSION.tgz" ]; then
        log "Скачивание Python $PYTHON_VERSION..."
        wget --progress=bar:force "https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz" 2>&1 | tee -a "../$LOG_FILE"
    else
        log "Архив Python уже скачан"
    fi
    
    # Распаковываем
    if [ ! -d "Python-$PYTHON_VERSION" ]; then
        log "Распаковка архива..."
        tar -xzf "Python-$PYTHON_VERSION.tgz"
    fi
    
    cd "Python-$PYTHON_VERSION"
    
    # Настройка сборки (без --prefix, чтобы не устанавливать в отдельную папку)
    log "Настройка сборки Python..."
    ./configure \
        --enable-optimizations \
        --with-lto \
        2>&1 | tee -a "../../$LOG_FILE"
    
    # Сборка
    log "Сборка Python (это может занять 10-15 минут)..."
    make -j$(nproc) 2>&1 | tee -a "../../$LOG_FILE"
    
    # Сохраняем путь к собранному Python (без установки)
    PYTHON_BIN="$(pwd)/python"
    
    cd ../..
    
    log_success "Python $PYTHON_VERSION собран (без установки в систему)"
    log "Путь к Python: $PYTHON_BIN"
}

create_virtual_environment() {
    log "Создание виртуального окружения из собранного Python..."
    
    # Проверяем, что Python существует
    if [ ! -f "$PYTHON_BIN" ]; then
        log_error "Собранный Python не найден: $PYTHON_BIN"
    fi
    
    # Создаём виртуальное окружение
    "$PYTHON_BIN" -m venv "$VENV_DIR" --without-pip 2>&1 | tee -a "$LOG_FILE"
    
    # Устанавливаем pip отдельно (важно для корректной работы)
    source "$VENV_DIR/bin/activate"
    curl -sS https://bootstrap.pypa.io/get-pip.py | python 2>&1 | tee -a "$LOG_FILE"
    
    log_success "Виртуальное окружение создано: $VENV_DIR"
}

upgrade_pip() {
    log "Обновление pip..."
    pip install --upgrade pip setuptools wheel 2>&1 | tee -a "$LOG_FILE"
    log_success "pip обновлён"
}

install_pytorch() {
    log "Установка PyTorch (CPU версия)..."
    
    # Устанавливаем CPU версию PyTorch
    pip install torch==2.4.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cpu 2>&1 | tee -a "$LOG_FILE"
    
    log_success "PyTorch установлен"
}

install_requirements() {
    log "Установка зависимостей из requirements.txt..."
    
    # Создаём requirements.txt если его нет
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        log "Создание requirements.txt..."
        cat > "$REQUIREMENTS_FILE" << 'EOF'
ruaccent>=1.5.0
PyPDF2>=3.0.0
ebooklib>=0.18
beautifulsoup4>=4.12.0
lxml>=4.9.0
TTS
scipy
numpy
PyQt5>=5.15.0
transformers==4.38.0
EOF
    fi
    
    # Устанавливаем зависимости
    pip install -r "$REQUIREMENTS_FILE" 2>&1 | tee -a "$LOG_FILE"
    
    log_success "Зависимости установлены"
}

verify_installation() {
    log "Проверка установки..."
    
    # Проверяем импорт ключевых модулей
    python -c "import torch; print(f'PyTorch {torch.__version__} OK')" 2>&1 | tee -a "$LOG_FILE"
    python -c "from TTS.api import TTS; print('XTTS OK')" 2>&1 | tee -a "$LOG_FILE"
    python -c "from ruaccent import RUAccent; print('ruaccent OK')" 2>&1 | tee -a "$LOG_FILE"
    python -c "import PyPDF2; import ebooklib; import bs4; import lxml; print('PDF/EPUB libraries OK')" 2>&1 | tee -a "$LOG_FILE"
    python -c "import scipy; import numpy; print('NumPy/SciPy OK')" 2>&1 | tee -a "$LOG_FILE"
    python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')" 2>&1 | tee -a "$LOG_FILE"
    
    # Специальная проверка для BeamSearchScorer
    python -c "from transformers import BeamSearchScorer; print('transformers BeamSearchScorer OK')" 2>&1 | tee -a "$LOG_FILE"
    
    log_success "Все модули импортируются успешно"
}

create_activation_script() {
    log "Создание скрипта активации окружения..."
    
    cat > "activate_env.sh" << 'EOF'
#!/bin/bash
# Скрипт для активации окружения
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/xtts_env/bin/activate"
echo "Окружение активировано. Запустите: python main.py"
EOF
    
    chmod +x "activate_env.sh"
    
    cat > "run.sh" << 'EOF'
#!/bin/bash
# Скрипт для запуска программы
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/xtts_env/bin/activate"
echo "Окружение активировано"
echo "Запуск программы..."
python main.py
deactivate
EOF
    
    chmod +x "run.sh"
    
    log_success "Созданы скрипты: activate_env.sh, run.sh"
}

print_completion_message() {
    local total_time=$1
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    УСТАНОВКА ЗАВЕРШЕНА!                          ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 Структура установки:"
    echo "   - Исходники Python: $PYTHON_SRC_DIR/"
    echo "   - Виртуальное окружение: $VENV_DIR/"
    echo "   - Лог установки: $LOG_FILE"
    echo ""
    echo "🚀 Для запуска программы:"
    echo "   1. Активируйте окружение:"
    echo "        source activate_env.sh"
    echo ""
    echo "   2. Скопируйте файлы программы в эту папку:"
    echo "        - main.py"
    echo "        - core/ (папка с модулями)"
    echo "        - gui/ (папка с GUI)"
    echo ""
    echo "   3. Запустите:"
    echo "        python main.py"
    echo "      или"
    echo "        ./run.sh"
    echo ""
    echo "⏱️  Общее время установки: $total_time секунд (~$((total_time / 60)) минут)"
    echo ""
    echo "📝 Примечания:"
    echo "   - При первом запуске XTTS скачает модель (~2 ГБ)"
    echo "   - Словарь ударений будет создан автоматически в рабочей папке"
    echo "   - Установлена совместимая версия transformers==4.38.0"
    echo ""
}

# =============================================================================
# Основной процесс
# =============================================================================

main() {
    local start_time=$(date +%s)
    
    print_banner
    
    # Очищаем лог
    > "$LOG_FILE"
    
    # Проверяем, что мы в чистом каталоге
    if [ -f "main.py" ] || [ -d "$VENV_DIR" ]; then
        log_warning "Кажется, установка уже была выполнена ранее"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Установка отменена"
            exit 0
        fi
    fi
    
    # Основные шаги
    check_system_dependencies
    download_and_build_python
    create_virtual_environment
    upgrade_pip
    install_pytorch
    install_requirements
    verify_installation
    create_activation_script
    
    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))
    
    print_completion_message "$total_time"
}

# Запуск
main "$@"
