#!/usr/bin/env python3
"""
Скрипт для миграции данных из SQLite в PostgreSQL
"""
import os
import sys
import sqlite3
import psycopg2
import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env.postgres
load_dotenv('../.env.postgres')

# Путь к SQLite базе данных
SQLITE_DB_PATH = "../loyalty.db"

# Получаем параметры подключения к PostgreSQL из переменных окружения
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Проверка существования SQLite базы данных
if not os.path.exists(SQLITE_DB_PATH):
    print(f"❌ SQLite база данных не найдена по пути: {SQLITE_DB_PATH}")
    sys.exit(1)

# Подключение к SQLite
try:
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row  # Это позволит получать результаты в виде словарей
    print(f"✅ Успешное подключение к SQLite ({SQLITE_DB_PATH})")
except Exception as e:
    print(f"❌ Ошибка подключения к SQLite: {e}")
    sys.exit(1)

# Подключение к PostgreSQL
try:
    pg_conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB
    )
    print(f"✅ Успешное подключение к PostgreSQL ({POSTGRES_HOST}:{POSTGRES_PORT})")
except Exception as e:
    print(f"❌ Ошибка подключения к PostgreSQL: {e}")
    sqlite_conn.close()
    sys.exit(1)

# Функция для получения количества записей в таблице
def count_rows(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    cursor.close()
    return count

# Функция для миграции данных между таблицами
def migrate_table(table_name, columns, id_column=None):
    print(f"\n📋 Миграция таблицы {table_name}...")
    
    # Получаем данные из SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"ℹ️ Таблица {table_name} пуста. Пропускаем.")
        return
    
    # Подготавливаем запрос для вставки в PostgreSQL
    pg_cursor = pg_conn.cursor()
    
    # Очищаем таблицу в PostgreSQL перед вставкой (если есть данные)
    pg_count = count_rows(pg_conn, table_name)
    if pg_count > 0:
        print(f"⚠️ В PostgreSQL уже есть {pg_count} записей в таблице {table_name}.")
        choice = input("Очистить таблицу перед миграцией? (y/n): ").strip().lower()
        if choice == 'y':
            pg_cursor.execute(f"DELETE FROM {table_name}")
            print(f"🗑️ Таблица {table_name} очищена.")
        else:
            print(f"⚠️ Возможно дублирование записей!")
    
    # Подготавливаем параметры для запроса
    placeholders = ', '.join(['%s'] * len(columns))
    insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    # Выполняем вставку данных
    try:
        for row in rows:
            # Преобразуем объект Row в список значений
            values = [row[col] for col in columns]
            pg_cursor.execute(insert_query, values)
        
        pg_conn.commit()
        print(f"✅ Успешно перенесено {len(rows)} записей в таблицу {table_name}")
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Ошибка при миграции таблицы {table_name}: {e}")
    finally:
        pg_cursor.close()
        sqlite_cursor.close()

# Выполняем миграцию для каждой таблицы
try:
    # 1. Таблица user_map
    migrate_table('user_map', ['tg_id', 'agent_id', 'phone', 'fullname'])
    
    # 2. Таблица bonuses
    migrate_table('bonuses', ['agent_id', 'balance'])
    
    # 3. Таблица accrual_log
    migrate_table('accrual_log', ['demand_id', 'processed_at'])
    
    # 4. Таблица loyalty_levels
    migrate_table('loyalty_levels', 
                 ['agent_id', 'level_id', 'total_spent', 'total_earned', 
                  'total_redeemed', 'created_at', 'updated_at'])
    
    # 5. Таблица bonus_transactions
    migrate_table('bonus_transactions', 
                 ['id', 'agent_id', 'transaction_type', 'amount', 
                  'description', 'related_demand_id', 'created_at'])
    
    # 6. Таблица maintenance_history
    migrate_table('maintenance_history', 
                 ['id', 'agent_id', 'work_id', 'performed_date', 'mileage', 
                  'source', 'demand_id', 'notes', 'created_at'])
    
    # 7. Таблица maintenance_settings
    migrate_table('maintenance_settings', 
                 ['agent_id', 'work_id', 'custom_mileage_interval', 
                  'custom_time_interval', 'is_active'])
    
    # 8. Таблица maintenance_service_mapping
    migrate_table('maintenance_service_mapping', 
                 ['moysklad_service_name', 'work_id', 'is_active'])
    
    # 9. Таблица user_achievements
    migrate_table('user_achievements', 
                 ['user_id', 'achievement_id', 'unlocked_at'])

    print("\n✅ Миграция данных успешно завершена")
    
except Exception as e:
    print(f"\n❌ Неожиданная ошибка при миграции данных: {e}")
finally:
    # Закрываем соединения
    sqlite_conn.close()
    pg_conn.close()
    print("🔄 Соединения с базами данных закрыты")
