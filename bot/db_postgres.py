"""
Модуль для работы с базой данных PostgreSQL.
Заменяет функциональность исходного db.py.
"""
import os
import logging
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Настройка логирования
log = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение настроек подключения
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Проверка настроек
if not all([POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    raise RuntimeError("Необходимо указать настройки PostgreSQL в файле .env или переменных окружения")

# Создание соединения с PostgreSQL
def get_connection():
    """Возвращает соединение с базой данных PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB
        )
        return conn
    except Exception as e:
        log.error(f"Ошибка подключения к PostgreSQL: {e}")
        raise

# Глобальное соединение для использования в функциях
try:
    conn = get_connection()
    # Настройка для автоматического коммита транзакций
    conn.autocommit = False
    log.info(f"Успешное подключение к PostgreSQL ({POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB})")
except Exception as e:
    log.error(f"Не удалось подключиться к PostgreSQL: {e}")
    raise

# Создание таблиц, если они не существуют
def init_database():
    """Инициализирует базу данных и создает необходимые таблицы"""
    try:
        with conn.cursor() as cursor:
            # Таблица user_map
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_map (
                tg_id BIGINT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                phone TEXT DEFAULT '',
                fullname TEXT DEFAULT ''
            )
            """)
            
            # Таблица bonuses
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bonuses (
                agent_id TEXT PRIMARY KEY,
                balance INTEGER NOT NULL DEFAULT 0
            )
            """)
            
            # Таблица accrual_log
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS accrual_log (
                demand_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Таблица loyalty_levels
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS loyalty_levels (
                agent_id TEXT PRIMARY KEY,
                level_id INTEGER NOT NULL DEFAULT 1,
                total_spent INTEGER NOT NULL DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                total_redeemed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
            )
            """)
            
            # Таблица bonus_transactions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bonus_transactions (
                id SERIAL PRIMARY KEY,
                agent_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT NOT NULL,
                related_demand_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
            )
            """)
            
            # Таблица maintenance_history
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_history (
                id SERIAL PRIMARY KEY,
                agent_id TEXT NOT NULL,
                work_id INTEGER NOT NULL,
                performed_date DATE NOT NULL,
                mileage INTEGER NOT NULL,
                source TEXT NOT NULL,
                demand_id TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
            )
            """)
            
            # Таблица maintenance_settings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_settings (
                agent_id TEXT NOT NULL,
                work_id INTEGER NOT NULL,
                custom_mileage_interval INTEGER,
                custom_time_interval INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                PRIMARY KEY (agent_id, work_id),
                FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
            )
            """)
            
            # Таблица maintenance_service_mapping
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_service_mapping (
                moysklad_service_name TEXT PRIMARY KEY,
                work_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
            """)
            
            # Таблица user_achievements
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id BIGINT,
                achievement_id TEXT,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id)
            )
            """)
            
            # Индексы
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_maintenance_history_agent_work 
                ON maintenance_history(agent_id, work_id)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_maintenance_history_date 
                ON maintenance_history(performed_date)
            """)
            
            conn.commit()
            log.info("База данных PostgreSQL успешно инициализирована")
    except Exception as e:
        conn.rollback()
        log.error(f"Ошибка инициализации базы данных: {e}")
        raise

# Инициализируем базу данных при импорте модуля
init_database()

# ─── функции для работы с пользователями ───────────────────────────────
def get_agent_id(tg_id: int) -> Optional[str]:
    """Получает ID агента (контрагента) по ID пользователя Telegram"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT agent_id FROM user_map WHERE tg_id=%s", (tg_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        log.error(f"Ошибка получения agent_id: {e}")
        return None


def register_mapping(tg_id: int, agent_id: str, phone: str, fullname: str):
    """Регистрирует связь между пользователем Telegram и агентом в МойСклад"""
    try:
        with conn.cursor() as cursor:
            # Добавляем или обновляем пользователя
            cursor.execute("""
            INSERT INTO user_map(tg_id, agent_id, phone, fullname)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT(tg_id) DO UPDATE
            SET agent_id = EXCLUDED.agent_id,
                phone = EXCLUDED.phone,
                fullname = EXCLUDED.fullname
            """, (tg_id, agent_id, phone, fullname))
            
            # Создаем запись баланса, если она не существует
            cursor.execute("""
            INSERT INTO bonuses(agent_id, balance) VALUES(%s, %s)
            ON CONFLICT(agent_id) DO NOTHING
            """, (agent_id, 10000))  # 100 бонусов для нового пользователя
            
            # Инициализируем уровень лояльности
            init_loyalty_level(agent_id)
            
            conn.commit()
            log.info(f"Регистрация пользователя: tg_id={tg_id}, agent_id={agent_id}")
    except Exception as e:
        conn.rollback()
        log.error(f"Ошибка регистрации пользователя: {e}")


def user_contact(tg_id: int) -> Tuple[str, str]:
    """Получает контактную информацию пользователя"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT phone, fullname FROM user_map WHERE tg_id=%s", (tg_id,))
            row = cursor.fetchone()
            return row if row else ("", "")
    except Exception as e:
        log.error(f"Ошибка получения контактных данных: {e}")
        return ("", "")


# ─── функции для работы с бонусами ───────────────────────────────────
def get_balance(agent_id: str) -> int:
    """Получает текущий баланс бонусов"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT balance FROM bonuses WHERE agent_id=%s", (agent_id,))
            row = cursor.fetchone()
            return row[0] if row else 0
    except Exception as e:
        log.error(f"Ошибка получения баланса: {e}")
        return 0


def change_balance(agent_id: str, delta: int):
    """Изменяет баланс бонусов на указанную величину"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO bonuses(agent_id, balance) VALUES(%s, %s)
            ON CONFLICT(agent_id) DO UPDATE SET balance = bonuses.balance + %s
            """, (agent_id, delta, delta))
            conn.commit()
            log.info(f"Изменение баланса: agent_id={agent_id}, delta={delta}")
    except Exception as e:
        conn.rollback()
        log.error(f"Ошибка изменения баланса: {e}")


def get_tg_id_by_agent(agent_id: str) -> Optional[int]:
    """Получает Telegram ID пользователя по его agent_id"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT tg_id FROM user_map WHERE agent_id=%s", (agent_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        log.error(f"Ошибка получения tg_id: {e}")
        return None


# ─── функции для работы с уровнями лояльности ───────────────────────
def init_loyalty_level(agent_id: str):
    """Инициализирует уровень лояльности для нового клиента"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO loyalty_levels(agent_id, level_id, total_spent)
            VALUES (%s, 1, 0)
            ON CONFLICT(agent_id) DO NOTHING
            """, (agent_id,))
            conn.commit()
            log.info(f"Инициализация уровня лояльности: agent_id={agent_id}")
    except Exception as e:
        conn.rollback()
        log.error(f"Ошибка инициализации уровня лояльности: {e}")


def get_loyalty_level(agent_id: str) -> Dict[str, int]:
    """Получает информацию об уровне лояльности клиента"""
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
            SELECT level_id, total_spent, total_earned, total_redeemed
            FROM loyalty_levels WHERE agent_id=%s
            """, (agent_id,))
            row = cursor.fetchone()
            
            if not row:
                init_loyalty_level(agent_id)
                return {"level_id": 1, "total_spent": 0, "total_earned": 0, "total_redeemed": 0}
            
            return dict(row)
    except Exception as e:
        log.error(f"Ошибка получения уровня лояльности: {e}")
        return {"level_id": 1, "total_spent": 0, "total_earned": 0, "total_redeemed": 0}


def update_total_spent(agent_id: str, amount: int) -> Dict[str, Any]:
    """Обновляет общую сумму трат и проверяет повышение уровня"""
    try:
        # Получаем текущий уровень
        current_data = get_loyalty_level(agent_id)
        new_total = current_data["total_spent"] + amount
        
        # Определяем новый уровень с помощью функции из модуля loyalty
        from .loyalty import calculate_level_by_spent
        new_level = calculate_level_by_spent(new_total)
        
        # Обновляем данные
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE loyalty_levels 
            SET total_spent = %s, level_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE agent_id = %s
            """, (new_total, new_level, agent_id))
            conn.commit()
        
        return {
            "old_level": current_data["level_id"],
            "new_level": new_level,
            "total_spent": new_total,
            "level_changed": new_level > current_data["level_id"]
        }
    except Exception as e:
        conn.rollback()
        log.error(f"Ошибка обновления трат: {e}")
        return {
            "old_level": current_data["level_id"],
            "new_level": current_data["level_id"],
            "total_spent": current_data["total_spent"],
            "level_changed": False
        }


def add_bonus_transaction(agent_id: str, transaction_type: str, amount: int, description: str, related_demand_id: str = None):
    """Добавляет запись о транзакции бонусов"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO bonus_transactions 
            (agent_id, transaction_type, amount, description, related_demand_id)
            VALUES (%s, %s, %s, %s, %s)
            """, (agent_id, transaction_type, amount, description, related_demand_id))
            
            # Обновляем соответствующий счетчик в таблице loyalty_levels
            if transaction_type == 'accrual':
                cursor.execute("""
                UPDATE loyalty_levels SET total_earned = total_earned + %s
                WHERE agent_id = %s
                """, (amount, agent_id))
            elif transaction_type == 'redemption':
                cursor.execute("""
                UPDATE loyalty_levels SET total_redeemed = total_redeemed + %s
                WHERE agent_id = %s
                """, (abs(amount), agent_id))
            
            conn.commit()
            log.info(f"Транзакция бонусов: agent_id={agent_id}, type={transaction_type}, amount={amount}")
    except Exception as e:
        conn.rollback()
        log.error(f"Ошибка добавления транзакции: {e}")


def get_bonus_transactions(agent_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Получает историю транзакций бонусов за указанный период"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
            SELECT transaction_type, amount, description, related_demand_id, created_at
            FROM bonus_transactions
            WHERE agent_id = %s AND created_at >= %s
            ORDER BY created_at DESC
            """, (agent_id, cutoff_date.isoformat()))
            rows = cursor.fetchall()
            
            return [
                {
                    "type": row["transaction_type"],
                    "amount": row["amount"],
                    "description": row["description"],
                    "related_demand_id": row["related_demand_id"],
                    "date": row["created_at"]
                }
                for row in rows
            ]
    except Exception as e:
        log.error(f"Ошибка получения истории транзакций: {e}")
        return []
