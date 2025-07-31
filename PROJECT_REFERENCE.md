# Справочник проекта Loyalty Bot

## Информация о среде разработки

### Рабочее окружение
- **Операционная система**: macOS
- **Домашняя директория**: `/Users/ilaeliseenko`
- **Текущая рабочая директория**: `/Users/ilaeliseenko/Desktop/loyalty-bot/admin`
- **Shell**: zsh 5.9
- **Текущее время**: 2025-07-26T16:57:04Z

### Доступные кодовые базы
1. **akpp-generator**
   - Путь: `/Users/ilaeliseenko/Desktop/akpp-generator`
   - Описание: Генератор для АКПП

2. **loyalty-bot** (текущий проект)
   - Путь: `/Users/ilaeliseenko/Desktop/loyalty-bot`
   - Описание: Система лояльности с ботом

## Структура проекта Loyalty Bot

### Основные компоненты
- **admin/** - Административная панель
- **miniapp/** - Мини-приложение
- **web-app/** - Веб-приложение
- **bot/** - Телеграм бот

### Документация проекта

#### Технические руководства
- `ADMIN_README.md` - Руководство по административной панели
- `ANALYTICS_README.md` - Документация по аналитике
- `START_GUIDE.md` - Руководство по запуску
- `USER_GUIDE.md` - Руководство пользователя
- `PRODUCTION_CHECKLIST.md` - Чек-лист для продакшена
- `PRODUCTION_DEPLOYMENT.md` - Руководство по развертыванию

#### Техническая информация
- `AUTHORIZATION_FIXES_SUMMARY.md` - Исправления авторизации
- `POSTGRES_MIGRATION.md` - Миграция PostgreSQL
- `MINIAPP_OVERVIEW.md` - Обзор мини-приложения

#### UX и дизайн
- `DESIGN_BRIEF.md` - Техническое задание на дизайн
- `UX_COPYWRITING_GUIDE.md` - Руководство по UX-копирайтингу
- `UX_DESIGN_OPTIMIZATION.md` - Оптимизация UX-дизайна
- `UX_IMPLEMENTATION_GUIDE.md` - Руководство по реализации UX
- `COPYWRITING_IMPLEMENTATION.md` - Реализация копирайтинга

#### Функциональность
- `BOT_FEATURES.md` - Функции бота
- `FINAL_SUMMARY.md` - Итоговое резюме

#### Тестирование
- `test_checklist.md` - Чек-лист тестирования

### Технологии
- **Frontend**: React (Create React App)
- **Backend**: Node.js/Express
- **База данных**: PostgreSQL
- **Среда разработки**: macOS с zsh

### Команды разработки

#### Веб-приложение
```bash
cd /Users/ilaeliseenko/Desktop/loyalty-bot/web-app
npm start    # Запуск в режиме разработки
npm test     # Запуск тестов
npm run build # Сборка для продакшена
```

#### Административная панель
```bash
cd /Users/ilaeliseenko/Desktop/loyalty-bot/admin
# Команды аналогичны веб-приложению
```

#### Мини-приложение
```bash
cd /Users/ilaeliseenko/Desktop/loyalty-bot/miniapp
# Команды для мини-приложения
```

## Полезные пути

### Директории проекта
- Корневая директория: `/Users/ilaeliseenko/Desktop/loyalty-bot`
- Административная панель: `/Users/ilaeliseenko/Desktop/loyalty-bot/admin`
- Веб-приложение: `/Users/ilaeliseenko/Desktop/loyalty-bot/web-app`
- Мини-приложение: `/Users/ilaeliseenko/Desktop/loyalty-bot/miniapp`

### Конфигурационные файлы
- `package.json` - в каждом модуле
- `.env` - переменные окружения
- Конфигурации webpack, babel, eslint - в соответствующих модулях

## Примечания
- Проект использует индексированную кодовую базу для семантического поиска
- Доступны инструменты для поиска и анализа кода
- Все модули имеют схожую структуру на базе Node.js/React

---
*Последнее обновление: 2025-07-26*
