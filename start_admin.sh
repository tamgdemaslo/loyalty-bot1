#!/bin/bash

# Скрипт для запуска администраторской панели системы лояльности

echo "🔧 Запуск администраторской панели..."

# Переходим в директорию админ панели
cd "$(dirname "$0")/admin"

# Проверяем, установлены ли зависимости
if [ ! -d "node_modules" ]; then
    echo "📦 Установка зависимостей..."
    npm install
fi

# Проверяем наличие базы данных
if [ ! -f "../loyalty.db" ]; then
    echo "❌ База данных не найдена!"
    echo "Убедитесь, что бот был запущен хотя бы один раз для создания базы данных."
    exit 1
fi

# Устанавливаем переменные окружения
export ADMIN_PORT=3001

echo "🚀 Запуск сервера админ панели..."
echo "📊 Панель будет доступна по адресу: http://localhost:3001"
echo "⏹️  Для остановки нажмите Ctrl+C"

# Запускаем сервер
npm start
