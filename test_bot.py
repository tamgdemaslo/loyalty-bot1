#!/usr/bin/env python3
"""
Тестовый запуск бота системы лояльности
Этот скрипт проверяет основные компоненты без реального подключения к Telegram
"""

import sys
import os
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s: %(message)s",
)

async def test_bot_components():
    """Тестирует основные компоненты бота"""
    print("🧪 Запуск тестирования компонентов бота...")
    print("=" * 50)
    
    # Тест 1: Импорт конфигурации
    print("\n1️⃣ Тестирование конфигурации...")
    try:
        from bot.config import BOT_TOKEN, MS_TOKEN, BONUS_RATE
        print(f"✅ Конфигурация загружена")
        print(f"   • BOT_TOKEN: {'✅ Установлен' if BOT_TOKEN else '❌ Не установлен'}")
        print(f"   • MS_TOKEN: {'✅ Установлен' if MS_TOKEN else '❌ Не установлен'}")
        print(f"   • BONUS_RATE: {BONUS_RATE}")
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False
    
    # Тест 2: База данных
    print("\n2️⃣ Тестирование базы данных...")
    try:
        from bot.db import initialize_db, get_user_bonuses
        await initialize_db()
        print("✅ База данных инициализирована")
        
        # Тестовая проверка пользователя
        test_user_id = 12345
        bonuses = await get_user_bonuses(test_user_id)
        print(f"✅ Тест запроса бонусов (пользователь {test_user_id}): {bonuses}")
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False
    
    # Тест 3: Утилиты
    print("\n3️⃣ Тестирование утилит...")
    try:
        from bot.utils import format_phone, calculate_bonus
        
        test_phone = "+7 (123) 456-78-90"
        formatted_phone = format_phone(test_phone)
        print(f"✅ Форматирование телефона: {test_phone} -> {formatted_phone}")
        
        test_amount = 1000
        bonus = calculate_bonus(test_amount)
        print(f"✅ Расчет бонуса: {test_amount} руб -> {bonus} бонусов")
    except Exception as e:
        print(f"❌ Ошибка утилит: {e}")
        return False
    
    # Тест 4: Клавиатуры
    print("\n4️⃣ Тестирование клавиатур...")
    try:
        from bot.keyboards import main_menu, services_menu
        
        main_kb = main_menu()
        print(f"✅ Главное меню: {len(main_kb.keyboard)} кнопок")
        
        services_kb = services_menu()
        print(f"✅ Меню услуг: {len(services_kb.keyboard)} кнопок")
    except Exception as e:
        print(f"❌ Ошибка клавиатур: {e}")
        return False
    
    # Тест 5: Система лояльности
    print("\n5️⃣ Тестирование системы лояльности...")
    try:
        from bot.loyalty import get_loyalty_level, calculate_discount
        
        test_bonuses = 500
        level = await get_loyalty_level(test_bonuses)
        print(f"✅ Уровень лояльности для {test_bonuses} бонусов: {level}")
        
        discount = calculate_discount(level)
        print(f"✅ Скидка для уровня {level}: {discount}%")
    except Exception as e:
        print(f"❌ Ошибка системы лояльности: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Все компоненты протестированы успешно!")
    return True

async def test_bot_handlers():
    """Тестирует обработчики команд (симуляция)"""
    print("\n🎭 Тестирование обработчиков команд...")
    print("=" * 50)
    
    try:
        from bot.handlers import register
        from aiogram import Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        
        # Создаем тестовый диспетчер
        dp = Dispatcher(storage=MemoryStorage())
        register(dp)
        
        print("✅ Обработчики зарегистрированы")
        print(f"   • Количество обработчиков: {len(dp.observers)}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка обработчиков: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования Telegram бота системы лояльности")
    print("📝 Режим: ТЕСТОВЫЙ (без подключения к Telegram)")
    print("🔧 Проверяем все компоненты системы...")
    
    success = True
    
    # Тестируем компоненты
    if not await test_bot_components():
        success = False
    
    # Тестируем обработчики
    if not await test_bot_handlers():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Бот готов к запуску в production режиме")
    else:
        print("❌ ЕСТЬ ОШИБКИ В ТЕСТАХ")
        print("🔧 Необходимо исправить проблемы перед запуском")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
