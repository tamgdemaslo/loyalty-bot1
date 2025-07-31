#!/bin/bash

# Скрипт развертывания loyalty-bot на сервере
echo "🚀 Запуск развертывания loyalty-bot..."

# Обновляем систему
echo "📦 Обновление системы..."
sudo apt-get update
sudo apt-get upgrade -y

# Устанавливаем Docker если не установлен
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
fi

# Устанавливаем Docker Compose если не установлен
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Установка Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Создаем директорию для проекта
mkdir -p ~/loyalty-bot
cd ~/loyalty-bot

# Распаковываем архив если он есть
if [ -f ~/loyalty-bot.tar.gz ]; then
    echo "📦 Распаковка проекта..."
    tar -xzf ~/loyalty-bot.tar.gz --strip-components=1
    rm ~/loyalty-bot.tar.gz
fi

# Создаем .env файл если его нет
if [ ! -f .env ]; then
    echo "⚙️ Создание файла конфигурации..."
    cat > .env << EOL
BOT_TOKEN=7914899311:AAGY4CjuMqZX3w1eS7zCM2yNMW3312xCwPE
MS_TOKEN=ecfb2a801095bded8b05cabbb597bbce3dc59e73
YCLIENTS_PARTNER_TOKEN=mz5bf2yp97nbs4s45e9j
MINIAPP_URL=http://176.123.161.29:3000
NODE_ENV=production
EOL
fi

# Создаем директории для данных
mkdir -p data

# Останавливаем предыдущие контейнеры если они запущены
echo "🛑 Остановка предыдущих контейнеров..."
docker-compose down 2>/dev/null || true

# Собираем и запускаем контейнеры
echo "🔨 Сборка и запуск контейнеров..."
docker-compose up --build -d

# Проверяем статус
echo "✅ Проверка статуса контейнеров..."
docker-compose ps

echo "🎉 Развертывание завершено!"
echo "📱 Telegram бот должен быть доступен"
echo "🌐 Mini App доступен по адресу: http://176.123.161.29:3000"
echo ""
echo "📊 Для просмотра логов используйте:"
echo "   docker-compose logs -f loyalty-bot"
echo "   docker-compose logs -f miniapp"
echo ""
echo "🛑 Для остановки используйте:"
echo "   docker-compose down"
