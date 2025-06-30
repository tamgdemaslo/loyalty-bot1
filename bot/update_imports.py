#!/usr/bin/env python3
"""
Скрипт для модификации импортов в Python-файлах бота.
Заменяет импорты из модуля db на db_postgres.

Запуск:
python update_imports.py
"""

import os
import re
import sys
from pathlib import Path


def update_imports_in_file(file_path):
    """
    Обновляет импорты из db на db_postgres в указанном файле.
    
    Args:
        file_path: Путь к файлу для обновления
    
    Returns:
        bool: True, если файл был изменен, False в противном случае
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Шаблоны для поиска импортов
    patterns = [
        (r'from \.db import', r'from .db_postgres import'),
        (r'from db import', r'from db_postgres import'),
        (r'import db', r'import db_postgres as db')
    ]
    
    modified = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Обновлены импорты в файле: {file_path}")
    
    return modified


def main():
    """
    Основная функция скрипта.
    Обходит все Python-файлы в директории бота и обновляет импорты.
    """
    # Получаем текущую директорию (должна быть директория бота)
    bot_dir = Path(__file__).parent
    
    # Проверяем, что db_postgres.py существует
    if not (bot_dir / "db_postgres.py").exists():
        print("Ошибка: Файл db_postgres.py не найден в директории бота")
        sys.exit(1)
    
    # Счетчики
    processed_files = 0
    modified_files = 0
    
    # Обрабатываем все Python-файлы в директории бота
    for root, _, files in os.walk(bot_dir):
        for file in files:
            if file.endswith('.py') and file != 'db_postgres.py' and file != 'update_imports.py':
                file_path = os.path.join(root, file)
                processed_files += 1
                if update_imports_in_file(file_path):
                    modified_files += 1
    
    print(f"\nОбработано файлов: {processed_files}")
    print(f"Модифицировано файлов: {modified_files}")
    print("\nОбновление импортов завершено.")
    
    if modified_files > 0:
        print("\nВажно: Необходимо проверить корректность работы бота после изменений.")
        print("Возможно, потребуется дополнительная настройка и тестирование.")


if __name__ == "__main__":
    main()
