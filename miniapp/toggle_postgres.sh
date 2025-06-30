#!/bin/bash

# Скрипт для переключения miniapp на использование PostgreSQL
echo "🔄 Переключение miniapp на PostgreSQL..."

# Копируем .env.postgres в .env
cat .env.postgres >> .env
echo "✅ Настройки PostgreSQL добавлены в .env"

# Проверка наличия модуля pg (PostgreSQL для Node.js)
if npm list pg | grep -q "pg@"; then
    echo "✅ Модуль pg уже установлен"
else
    echo "📦 Установка модуля pg..."
    npm install pg
fi

# Удаляем модуль sqlite3, если он есть
if npm list sqlite3 | grep -q "sqlite3@"; then
    echo "🗑️ Удаление модуля sqlite3..."
    npm uninstall sqlite3
fi

# Удаляем файлы SQLite
if [ -f "api_integration.js" ]; then
    echo "🗑️ Удаление api_integration.js..."
    rm api_integration.js
fi

if [ -f "api_integration_simple.js" ]; then
    echo "🗑️ Удаление api_integration_simple.js..."
    rm api_integration_simple.js
fi

# Запускаем обновление сервера
echo "🔄 Обновление server.js для использования PostgreSQL..."
node update_server_postgres.js || echo "⚠️ Ошибка обновления server.js. Возможно, он уже использует PostgreSQL."

echo "✅ Переключение на PostgreSQL завершено!"
echo "Теперь вы можете запустить сервер командой: node server.js"
