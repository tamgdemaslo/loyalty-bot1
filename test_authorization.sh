#!/bin/bash

echo "🔧 Тестирование авторизации в loyalty-bot"
echo ""

# Остановка всех процессов
echo "⏹️  Остановка процессов..."
pkill -f "python.*bot" 2>/dev/null || true
pkill -f "node.*server" 2>/dev/null || true
sleep 2

# Запуск мини-приложения
echo "📱 Запуск мини-приложения..."
cd miniapp && node server.js &
MINIAPP_PID=$!
echo "Mini-app PID: $MINIAPP_PID"

# Ждем запуска сервера
sleep 3

echo ""
echo "✅ Мини-приложение запущено на http://localhost:3000"
echo ""
echo "🧪 Сценарии для тестирования:"
echo ""
echo "1. 📝 Авторизация через бота:"
echo "   - Откройте @tgmclientbot в Telegram"
echo "   - Выполните /start"
echo "   - Поделитесь номером телефона"
echo "   - После авторизации откройте приложение через кнопку в боте"
echo ""
echo "2. 🔒 Неавторизованный доступ:"
echo "   - Откройте http://localhost:3000/debug.html"
echo "   - Попробуйте доступ без данных Telegram"
echo "   - Должно показать экран авторизации"
echo ""
echo "3. 📱 Регистрация через приложение:"
echo "   - Если пользователь новый, должна показаться форма регистрации"
echo "   - Заполните имя и телефон"
echo "   - Получите приветственные бонусы"
echo ""
echo "Для остановки нажмите Ctrl+C"

# Функция для graceful shutdown
cleanup() {
    echo ""
    echo "⏹️  Остановка мини-приложения..."
    kill $MINIAPP_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Ждем сигнал для остановки
wait
