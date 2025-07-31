# 🚀 Инструкция по развертыванию Loyalty Bot на сервере

## 📋 Что нужно для развертывания

- Сервер с Ubuntu/Debian
- SSH доступ к серверу (user1@176.123.161.29)
- Docker и Docker Compose на сервере

## 🔧 Пошаговое развертывание

### Шаг 1: Подключение к серверу

```bash
ssh user1@176.123.161.29
```

### Шаг 2: Загрузка проекта на сервер

Вариант A - Скопировать архив:
```bash
# На локальной машине
scp loyalty-bot.tar.gz user1@176.123.161.29:~/
```

Вариант B - Клonировать через Git (если есть репозиторий):
```bash
git clone [URL_репозитория] ~/loyalty-bot
```

### Шаг 3: Запуск скрипта установки

```bash
# На сервере
cd ~
chmod +x ~/loyalty-bot/deploy.sh
./loyalty-bot/deploy.sh
```

## 🐳 Ручная установка Docker (если нужно)

```bash
# Обновление системы
sudo apt-get update
sudo apt-get upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезапуск сессии для применения изменений группы
newgrp docker
```

## 🚀 Запуск проекта

### Если используете docker-compose.yml:

```bash
cd ~/loyalty-bot

# Создание .env файла
cat > .env << EOL
BOT_TOKEN=7914899311:AAGY4CjuMqZX3w1eS7zCM2yNMW3312xCwPE
MS_TOKEN=ecfb2a801095bded8b05cabbb597bbce3dc59e73
YCLIENTS_PARTNER_TOKEN=mz5bf2yp97nbs4s45e9j
MINIAPP_URL=http://176.123.161.29:3000
NODE_ENV=production
EOL

# Запуск контейнеров
docker-compose up --build -d
```

### Если используете простой Docker:

```bash
# Сборка образа для бота
docker build -f Dockerfile.bot -t loyalty-bot .

# Запуск бота
docker run -d \
  --name loyalty-bot \
  --restart unless-stopped \
  -e BOT_TOKEN=7914899311:AAGY4CjuMqZX3w1eS7zCM2yNMW3312xCwPE \
  -e MS_TOKEN=ecfb2a801095bded8b05cabbb597bbce3dc59e73 \
  -e YCLIENTS_PARTNER_TOKEN=mz5bf2yp97nbs4s45e9j \
  -e MINIAPP_URL=http://176.123.161.29:3000 \
  -v $(pwd)/loyalty.db:/app/loyalty.db \
  loyalty-bot

# Сборка и запуск miniapp
cd miniapp
docker build -f ../Dockerfile -t loyalty-miniapp .
docker run -d \
  --name loyalty-miniapp \
  --restart unless-stopped \
  -p 3000:3000 \
  -e NODE_ENV=production \
  -v $(pwd)/../loyalty.db:/app/loyalty.db \
  loyalty-miniapp
```

## 📊 Полезные команды

### Просмотр логов:
```bash
# Логи бота
docker logs -f loyalty-bot

# Логи miniapp
docker logs -f loyalty-miniapp

# Логи через docker-compose
docker-compose logs -f
```

### Управление контейнерами:
```bash
# Просмотр статуса
docker ps
docker-compose ps

# Остановка
docker stop loyalty-bot loyalty-miniapp
docker-compose down

# Перезапуск
docker restart loyalty-bot loyalty-miniapp
docker-compose restart

# Обновление (пересборка)
docker-compose up --build -d
```

### Проверка работы:
```bash
# Проверка портов
sudo netstat -tlnp | grep 3000

# Тест Mini App
curl http://176.123.161.29:3000

# Проверка базы данных
ls -la loyalty.db
```

## 🔧 Настройка автозапуска

Контейнеры с флагом `--restart unless-stopped` будут автоматически запускаться при перезагрузке сервера.

Для дополнительной надежности можно создать systemd сервис:

```bash
sudo nano /etc/systemd/system/loyalty-bot.service
```

```ini
[Unit]
Description=Loyalty Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user1/loyalty-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable loyalty-bot.service
sudo systemctl start loyalty-bot.service
```

## ✅ Проверка развертывания

1. **Telegram Bot**: Напишите боту /start
2. **Mini App**: Откройте http://176.123.161.29:3000
3. **Логи**: Проверьте отсутствие ошибок в логах
4. **База данных**: Убедитесь что файл loyalty.db создается и обновляется

## 🚨 Решение проблем

### Бот не отвечает:
- Проверьте токен бота
- Убедитесь что контейнер запущен: `docker ps`
- Проверьте логи: `docker logs loyalty-bot`

### Mini App не открывается:
- Проверьте что порт 3000 открыт: `sudo ufw allow 3000`
- Проверьте статус контейнера: `docker ps`
- Проверьте логи: `docker logs loyalty-miniapp`

### Проблемы с базой данных:
- Убедитесь что файл loyalty.db имеет правильные права: `chmod 666 loyalty.db`
- Проверьте монтирование volumes в docker-compose.yml

## 🎉 Готово!

После успешного развертывания:
- 📱 Telegram бот работает круглосуточно
- 🌐 Mini App доступен по адресу http://176.123.161.29:3000
- 🔄 Автоматический перезапуск при сбоях
- 📊 Логирование всех операций
