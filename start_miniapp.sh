#!/bin/bash

echo "🚀 Запуск Telegram Mini App системы лояльности..."
echo "=" * 50

# Переходим в директорию miniapp
cd "$(dirname "$0")/miniapp"

# Проверяем, установлены ли зависимости
if [ ! -d "node_modules" ]; then
    echo "📦 Установка зависимостей..."
    npm install
fi

# Создаем .env файл если его нет
if [ ! -f ".env" ]; then
    echo "⚙️ Создание файла конфигурации..."
    cat > .env << EOF
BOT_TOKEN=7914899311:AAGY4CjuMqZX3w1eS7zCM2yNMW3312xCwPE
PORT=3000
NODE_ENV=development
EOF
    echo "✅ Файл .env создан"
fi

echo ""
echo "🌟 Mini App включает:"
echo "   • Система бонусов и лояльности"
echo "   • Онлайн запись на обслуживание" 
echo "   • История посещений и транзакций"
echo "   • Техническое обслуживание"
echo "   • Профиль пользователя"
echo "   • Адаптивный дизайн для мобильных"
echo ""
echo "📱 Для тестирования в Telegram:"
echo "   1. Используйте ngrok: npx ngrok http 3000"
echo "   2. Укажите URL в @BotFather"
echo "   3. Создайте Web App через /newapp"
echo ""
echo "🌐 Локальный доступ: http://localhost:3000"
echo "⏹️  Для остановки нажмите Ctrl+C"
echo "=" * 50

# Запускаем сервер
npm start
