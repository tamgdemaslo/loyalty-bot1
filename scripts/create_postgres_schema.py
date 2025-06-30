#!/usr/bin/env python3
"""
Скрипт для создания схемы базы данных PostgreSQL
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env.postgres
load_dotenv('../.env.postgres')

# Получаем параметры подключения из переменных окружения
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Проверяем, что все необходимые переменные окружения установлены
if not all([POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    print("Ошибка: Не все переменные окружения для PostgreSQL установлены.")
    print("Убедитесь, что файл .env.postgres содержит все необходимые настройки.")
    sys.exit(1)

# Устанавливаем соединение с PostgreSQL
try:
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB
    )
    print(f"✅ Успешное подключение к PostgreSQL ({POSTGRES_HOST}:{POSTGRES_PORT})")
except Exception as e:
    print(f"❌ Ошибка подключения к PostgreSQL: {e}")
    sys.exit(1)

# Создаем курсор для выполнения SQL-запросов
cursor = conn.cursor()

# SQL для создания таблиц (адаптировано из SQLite схемы)
create_tables = """
-- Таблица связи Telegram ID и Agent ID
CREATE TABLE IF NOT EXISTS user_map (
    tg_id BIGINT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    phone TEXT DEFAULT '',
    fullname TEXT DEFAULT ''
);

-- Таблица с балансом бонусов
CREATE TABLE IF NOT EXISTS bonuses (
    agent_id TEXT PRIMARY KEY,
    balance INTEGER NOT NULL DEFAULT 0
);

-- Журнал начислений
CREATE TABLE IF NOT EXISTS accrual_log (
    demand_id TEXT PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Уровни лояльности
CREATE TABLE IF NOT EXISTS loyalty_levels (
    agent_id TEXT PRIMARY KEY,
    level_id INTEGER NOT NULL DEFAULT 1,
    total_spent INTEGER NOT NULL DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    total_redeemed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
);

-- Транзакции бонусов
CREATE TABLE IF NOT EXISTS bonus_transactions (
    id SERIAL PRIMARY KEY,
    agent_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL, -- 'accrual' или 'redemption'
    amount INTEGER NOT NULL,
    description TEXT NOT NULL,
    related_demand_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
);

-- История технического обслуживания
CREATE TABLE IF NOT EXISTS maintenance_history (
    id SERIAL PRIMARY KEY,
    agent_id TEXT NOT NULL,
    work_id INTEGER NOT NULL,
    performed_date DATE NOT NULL,
    mileage INTEGER NOT NULL,
    source TEXT NOT NULL, -- 'auto' (из МойСклад) или 'manual' (ручной ввод)
    demand_id TEXT, -- ID отгрузки из МойСклад (если source='auto')
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
);

-- Настройки ТО
CREATE TABLE IF NOT EXISTS maintenance_settings (
    agent_id TEXT NOT NULL,
    work_id INTEGER NOT NULL,
    custom_mileage_interval INTEGER,
    custom_time_interval INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (agent_id, work_id),
    FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
);

-- Маппинг услуг МойСклад на работы ТО
CREATE TABLE IF NOT EXISTS maintenance_service_mapping (
    moysklad_service_name TEXT PRIMARY KEY,
    work_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Достижения пользователей
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id BIGINT,
    achievement_id TEXT,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, achievement_id)
);

-- Индексы для ускорения запросов
CREATE INDEX IF NOT EXISTS idx_maintenance_history_agent_work 
    ON maintenance_history(agent_id, work_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_history_date 
    ON maintenance_history(performed_date);
"""

try:
    # Выполняем SQL-скрипт для создания таблиц
    cursor.execute(create_tables)
    conn.commit()
    print("✅ Таблицы успешно созданы в PostgreSQL")
except Exception as e:
    conn.rollback()
    print(f"❌ Ошибка при создании таблиц: {e}")
    sys.exit(1)
finally:
    cursor.close()
    conn.close()

print("✅ Схема PostgreSQL успешно создана")
