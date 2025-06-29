#!/bin/bash

echo "🚀 Запуск тестирования loyalty-bot..."

# Остановка существующих процессов
echo "⏹️  Остановка существующих процессов..."
pkill -f "python.*bot" 2>/dev/null || true
pkill -f "node.*server" 2>/dev/null || true
sleep 2

# Запуск мини-приложения в фоне
echo "📱 Запуск мини-приложения..."
cd miniapp && node server.js &
MINIAPP_PID=$!
echo "Mini-app PID: $MINIAPP_PID"

# Ждем немного для запуска сервера
sleep 3

# Запуск бота в фоне
echo "🤖 Запуск Telegram бота..."
cd ..
python3 -m bot.main &
BOT_PID=$!
echo "Bot PID: $BOT_PID"

echo ""
echo "✅ Приложение запущено!"
echo "📱 Мини-приложение: http://localhost:3000"
echo "🤖 Telegram бот: @tgmclientbot"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo "Или выполните: kill $MINIAPP_PID $BOT_PID"

# Функция для graceful shutdown
cleanup() {
    echo ""
    echo "⏹️  Остановка приложений..."
    kill $MINIAPP_PID 2>/dev/null || true
    kill $BOT_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Ждем сигнал для остановки
wait
