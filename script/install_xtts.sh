#!/bin/bash
# =============================================================================
# Скрипт для диагностики и скачивания модели XTTS-v2
# =============================================================================

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфигурация
MODEL_NAME="tts_models/multilingual/multi-dataset/xtts_v2"
MODEL_DIR="$HOME/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"
TEMP_DIR="/tmp/xtts_download"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Диагностика и скачивание модели XTTS-v2             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Проверка сетевых источников
echo -e "${YELLOW}[1/5] Проверка доступности источников...${NC}"

SOURCES=(
    "https://huggingface.co"
    "https://coqui.gumroad.com"
    "https://github.com"
)

for source in "${SOURCES[@]}"; do
    if curl -s --connect-timeout 5 --max-time 10 "$source" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $source - доступен"
    else
        echo -e "  ${RED}✗${NC} $source - недоступен"
    fi
done
echo ""

# 2. Проверка текущего состояния модели
echo -e "${YELLOW}[2/5] Проверка наличия модели...${NC}"

if [ -d "$MODEL_DIR" ]; then
    MODEL_SIZE=$(du -sh "$MODEL_DIR" 2>/dev/null | cut -f1)
    FILE_COUNT=$(find "$MODEL_DIR" -type f 2>/dev/null | wc -l)
    echo -e "  ${GREEN}✓${NC} Модель найдена: $MODEL_DIR"
    echo -e "  ${BLUE}  Размер: $MODEL_SIZE, файлов: $FILE_COUNT${NC}"
    
    # Проверяем целостность
    if [ -f "$MODEL_DIR/model.pth" ]; then
        PTH_SIZE=$(stat -c%s "$MODEL_DIR/model.pth" 2>/dev/null || stat -f%z "$MODEL_DIR/model.pth" 2>/dev/null)
        EXPECTED_SIZE=2000000000  # ~2GB
        if [ "$PTH_SIZE" -gt "$EXPECTED_SIZE" ]; then
            echo -e "  ${GREEN}✓${NC} Файл model.pth существует и имеет нормальный размер"
        else
            echo -e "  ${RED}✗${NC} Файл model.pth повреждён или неполный"
            echo -e "  ${YELLOW}  Рекомендуется удалить папку и скачать заново${NC}"
        fi
    fi
else
    echo -e "  ${YELLOW}!${NC} Модель не найдена"
fi
echo ""

# 3. Проверка интернет-соединения
echo -e "${YELLOW}[3/5] Проверка скорости соединения...${NC}"

# Тест скорости до HuggingFace
HF_PING=$(curl -s -o /dev/null -w "%{time_total}" --connect-timeout 5 https://huggingface.co 2>/dev/null)
if [ -n "$HF_PING" ]; then
    echo -e "  ${GREEN}✓${NC} HuggingFace: ${HF_PING} секунд"
else
    echo -e "  ${RED}✗${NC} HuggingFace: таймаут"
fi
echo ""

# 4. Скачивание модели (если нужно)
echo -e "${YELLOW}[4/5] Скачивание модели...${NC}"

if [ -d "$MODEL_DIR" ] && [ "$(find "$MODEL_DIR" -name "model.pth" -size +1G 2>/dev/null)" ]; then
    echo -e "  ${GREEN}✓${NC} Модель уже скачана и выглядит целой"
    echo -e "  ${BLUE}  Для принудительного перескачивания удалите папку:${NC}"
    echo -e "  ${BLUE}  rm -rf $MODEL_DIR${NC}"
else
    echo -e "  ${YELLOW}!${NC} Начинаю скачивание модели XTTS-v2 (1.87 GB)..."
    echo -e "  ${BLUE}  Это может занять 5-30 минут в зависимости от скорости интернета${NC}"
    echo ""
    
    # Создаём временную директорию
    mkdir -p "$TEMP_DIR"
    
    # Активируем окружение
    source xtts_env/bin/activate
    
    # Скачиваем с помощью Python
    python -c "
import sys
import time

print('  Загрузка модели XTTS-v2...')
print('  Пожалуйста, подождите, прогресс будет отображаться...')
sys.stdout.flush()

from TTS.api import TTS

try:
    # Устанавливаем таймаут для requests
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    # Скачиваем модель
    tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
    print('\n  ✅ Модель успешно загружена!')
    
except Exception as e:
    print(f'\n  ❌ Ошибка: {e}')
    sys.exit(1)
"
    
    # Проверяем результат
    if [ -f "$MODEL_DIR/model.pth" ]; then
        echo -e "\n  ${GREEN}✓${NC} Модель успешно скачана!"
    else
        echo -e "\n  ${RED}✗${NC} Не удалось скачать модель"
    fi
fi
echo ""

# 5. Итоговая информация
echo -e "${YELLOW}[5/5] Итоговая информация...${NC}"

if [ -d "$MODEL_DIR" ]; then
    MODEL_SIZE=$(du -sh "$MODEL_DIR" 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}✓${NC} Модель готова к использованию"
    echo -e "  ${BLUE}  Путь: $MODEL_DIR${NC}"
    echo -e "  ${BLUE}  Размер: $MODEL_SIZE${NC}"
else
    echo -e "  ${RED}✗${NC} Модель не скачана"
    echo -e "  ${YELLOW}  Попробуйте запустить скрипт ещё раз или проверьте интернет${NC}"
fi

echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Готово!${NC} Запустите программу: ${BLUE}./run.sh${NC}"