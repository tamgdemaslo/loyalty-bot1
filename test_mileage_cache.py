#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функциональности кэширования пробега
"""

import sys
import os
import time
from datetime import datetime

# Добавляем путь к модулям бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

try:
    from bot.maintenance import (
        get_current_mileage, 
        get_cached_mileage, 
        update_mileage_cache,
        fetch_current_mileage_from_api,
        init_maintenance_tables
    )
    from bot.db import conn
    print("✅ Модули успешно импортированы")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_cache_operations():
    """Тестирует базовые операции с кэшем"""
    print("\n🧪 Тестирование базовых операций с кэшем...")
    
    test_agent_id = "test_agent_123"
    test_mileage = 12345
    
    # Тест 1: Обновление кэша
    print(f"1. Сохраняем в кэш: agent_id={test_agent_id}, mileage={test_mileage}")
    result = update_mileage_cache(test_agent_id, test_mileage)
    if result:
        print("✅ Кэш успешно обновлен")
    else:
        print("❌ Ошибка при обновлении кэша")
        return False
    
    # Тест 2: Получение из кэша
    print("2. Получаем данные из кэша...")
    cached_value = get_cached_mileage(test_agent_id)
    if cached_value == test_mileage:
        print(f"✅ Кэш работает правильно: {cached_value}")
    else:
        print(f"❌ Неверное значение из кэша: ожидали {test_mileage}, получили {cached_value}")
        return False
    
    # Тест 3: Проверка истечения кэша
    print("3. Проверяем истечение кэша (0 часов)...")
    expired_value = get_cached_mileage(test_agent_id, cache_hours=0)
    if expired_value is None:
        print("✅ Кэш корректно истекает")
    else:
        print(f"❌ Кэш не истекает: получили {expired_value}")
        return False
    
    return True

def test_get_current_mileage():
    """Тестирует основную функцию получения пробега"""
    print("\n🧪 Тестирование функции get_current_mileage...")
    
    test_agent_id = "test_agent_456"
    
    # Тест 1: Получение без кэша (должен вызвать API)
    print("1. Первый вызов (без кэша)...")
    start_time = time.time()
    mileage1 = get_current_mileage(test_agent_id)
    api_time = time.time() - start_time
    print(f"   Результат: {mileage1}, время: {api_time:.2f}с")
    
    # Тест 2: Повторный вызов (должен использовать кэш)
    print("2. Повторный вызов (из кэша)...")
    start_time = time.time()
    mileage2 = get_current_mileage(test_agent_id)
    cache_time = time.time() - start_time
    print(f"   Результат: {mileage2}, время: {cache_time:.2f}с")
    
    if mileage1 == mileage2:
        print("✅ Значения совпадают")
    else:
        print(f"❌ Значения не совпадают: {mileage1} != {mileage2}")
        return False
    
    if cache_time < api_time:
        print(f"✅ Кэш быстрее API: {cache_time:.2f}с < {api_time:.2f}с")
    else:
        print(f"⚠️ Кэш не быстрее API: {cache_time:.2f}с >= {api_time:.2f}с")
    
    # Тест 3: Принудительное обновление
    print("3. Принудительное обновление...")
    start_time = time.time()
    mileage3 = get_current_mileage(test_agent_id, force_update=True)
    force_time = time.time() - start_time
    print(f"   Результат: {mileage3}, время: {force_time:.2f}с")
    
    return True

def test_database_structure():
    """Проверяет структуру базы данных"""
    print("\n🧪 Проверка структуры базы данных...")
    
    try:
        cursor = conn.cursor()
        
        # Проверяем наличие таблицы
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='mileage_cache'
        """)
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Таблица mileage_cache существует")
        else:
            print("❌ Таблица mileage_cache не найдена")
            return False
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(mileage_cache)")
        columns = cursor.fetchall()
        
        expected_columns = ['agent_id', 'current_mileage', 'updated_at']
        actual_columns = [col[1] for col in columns]
        
        print(f"   Столбцы таблицы: {actual_columns}")
        
        for col in expected_columns:
            if col in actual_columns:
                print(f"   ✅ Столбец {col} найден")
            else:
                print(f"   ❌ Столбец {col} не найден")
                return False
        
        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) FROM mileage_cache")
        count = cursor.fetchone()[0]
        print(f"   📊 Записей в кэше: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")
        return False

def cleanup_test_data():
    """Очищает тестовые данные"""
    print("\n🧹 Очистка тестовых данных...")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mileage_cache WHERE agent_id LIKE 'test_agent_%'")
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ Удалено {deleted} тестовых записей")
        return True
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов кэширования пробега")
    print("=" * 50)
    
    # Инициализируем таблицы
    print("📋 Инициализация таблиц...")
    init_maintenance_tables()
    
    # Запускаем тесты
    tests = [
        ("Структура БД", test_database_structure),
        ("Операции с кэшем", test_cache_operations),
        ("Функция get_current_mileage", test_get_current_mileage),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name}: ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")
    
    # Очищаем тестовые данные
    cleanup_test_data()
    
    # Итоги
    print(f"\n{'='*50}")
    print(f"📊 Результаты тестирования:")
    print(f"   Пройдено: {passed}/{total}")
    print(f"   Процент успеха: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("⚠️ Некоторые тесты провалены")
        return 1

if __name__ == "__main__":
    sys.exit(main())
