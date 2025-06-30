#!/usr/bin/env python3
"""
Запуск Telegram бота системы лояльности
"""

import sys
import os
import asyncio
import logging

# Добавляем путь к проекту в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import main

if __name__ == "__main__":
    print("🚀 Запуск Telegram бота системы лояльности...")
    print("📱 Бот включает:")
    print("   • Система бонусов и лояльности")
    print("   • Онлайн запись на услуги")
    print("   • История посещений")
    print("   • Техническое обслуживание")
    print("   • Аналитика и статистика")
    print("   • Многоуровневая система статусов")
    print()
    print("⏹️  Для остановки бота нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске бота: {e}")
        sys.exit(1)
