#!/bin/bash
# Скрипт для активации окружения
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/xtts_env/bin/activate"
echo "Окружение активировано. Запустите: python main.py"
