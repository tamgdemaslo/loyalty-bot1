import sqlite3
from typing import Optional

conn = sqlite3.connect("loyalty.db")
conn.execute("PRAGMA foreign_keys=ON")

# ── гарантируем, что все нужные колонки и таблицы есть ───────────────
conn.executescript("""
CREATE TABLE IF NOT EXISTS user_map (
    tg_id    INTEGER PRIMARY KEY,
    agent_id TEXT    NOT NULL,
    phone    TEXT    DEFAULT '',
    fullname TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS bonuses (
    agent_id TEXT PRIMARY KEY,
    balance  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS accrual_log (
    demand_id    TEXT PRIMARY KEY,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loyalty_levels (
    agent_id TEXT PRIMARY KEY,
    level_id INTEGER NOT NULL DEFAULT 1,
    total_spent INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
);

CREATE TABLE IF NOT EXISTS bonus_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL, -- 'accrual' или 'redemption'
    amount INTEGER NOT NULL,
    description TEXT NOT NULL,
    related_demand_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES bonuses(agent_id)
);
""")
conn.commit()
# ─────────────────────────────────────────────────────────────────────

# ── helpers ──────────────────────────────────────────────────────────
def get_agent_id(tg_id: int) -> Optional[str]:
    row = conn.execute("SELECT agent_id FROM user_map WHERE tg_id=?", (tg_id,)).fetchone()
    return row[0] if row else None


def register_mapping(tg_id: int, agent_id: str, phone: str, fullname: str):
    conn.execute(
        """
        INSERT INTO user_map(tg_id, agent_id, phone, fullname)
        VALUES (?,?,?,?)
        ON CONFLICT(tg_id) DO UPDATE
           SET agent_id = excluded.agent_id,
               phone    = excluded.phone,
               fullname = excluded.fullname
        """,
        (tg_id, agent_id, phone, fullname),
    )
    # Начисление приветственных бонусов, если пользователь новый
    conn.execute(
        """
        INSERT INTO bonuses(agent_id, balance) VALUES(?,?)
        ON CONFLICT(agent_id) DO NOTHING
        """,
        (agent_id, 10000),  # 100 бонусов для нового пользователя
    )
    # Инициализируем уровень лояльности
    init_loyalty_level(agent_id)
    conn.commit()


def user_contact(tg_id: int) -> tuple[str, str]:
    row = conn.execute("SELECT phone, fullname FROM user_map WHERE tg_id=?", (tg_id,)).fetchone()
    return row if row else ("", "")


def get_balance(agent_id: str) -> int:
    row = conn.execute("SELECT balance FROM bonuses WHERE agent_id=?", (agent_id,)).fetchone()
    return row[0] if row else 0


def change_balance(agent_id: str, delta: int):
    conn.execute(
        """
        INSERT INTO bonuses(agent_id, balance) VALUES(?,?)
        ON CONFLICT(agent_id) DO UPDATE SET balance = balance + ?
        """,
        (agent_id, delta, delta),
    )
    conn.commit()


def get_tg_id_by_agent(agent_id: str) -> int | None:
    """Получает Telegram ID пользователя по его agent_id"""
    row = conn.execute(
        "SELECT tg_id FROM user_map WHERE agent_id=?", 
        (agent_id,)
    ).fetchone()
    return row[0] if row else None


# ── функции для работы с уровнями лояльности ──────────────────────────
def init_loyalty_level(agent_id: str):
    """Инициализирует уровень лояльности для нового клиента"""
    conn.execute(
        """
        INSERT INTO loyalty_levels(agent_id, level_id, total_spent)
        VALUES (?, 1, 0)
        ON CONFLICT(agent_id) DO NOTHING
        """,
        (agent_id,)
    )
    conn.commit()


def get_loyalty_level(agent_id: str) -> dict:
    """Получает информацию об уровне лояльности клиента"""
    row = conn.execute(
        "SELECT level_id, total_spent FROM loyalty_levels WHERE agent_id=?",
        (agent_id,)
    ).fetchone()
    
    if not row:
        init_loyalty_level(agent_id)
        return {"level_id": 1, "total_spent": 0}
    
    return {"level_id": row[0], "total_spent": row[1]}


def update_total_spent(agent_id: str, amount: int) -> dict:
    """Обновляет общую сумму трат и проверяет повышение уровня"""
    # Получаем текущий уровень
    current_data = get_loyalty_level(agent_id)
    new_total = current_data["total_spent"] + amount
    
    # Определяем новый уровень
    new_level = calculate_level_by_spent(new_total)
    
    # Обновляем данные
    conn.execute(
        """
        UPDATE loyalty_levels 
        SET total_spent = ?, level_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE agent_id = ?
        """,
        (new_total, new_level, agent_id)
    )
    conn.commit()
    
    return {
        "old_level": current_data["level_id"],
        "new_level": new_level,
        "total_spent": new_total,
        "level_changed": new_level > current_data["level_id"]
    }


def add_bonus_transaction(agent_id: str, transaction_type: str, amount: int, description: str, related_demand_id: str = None):
    """Добавляет запись о транзакции бонусов"""
    conn.execute(
        """
        INSERT INTO bonus_transactions (agent_id, transaction_type, amount, description, related_demand_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (agent_id, transaction_type, amount, description, related_demand_id)
    )
    conn.commit()


def get_bonus_transactions(agent_id: str, days: int = 30) -> list:
    """Получает историю транзакций бонусов за указанный период"""
    cutoff_date = datetime.now() - timedelta(days=days)
    rows = conn.execute(
        """
        SELECT transaction_type, amount, description, related_demand_id, created_at
        FROM bonus_transactions
        WHERE agent_id = ? AND created_at >= ?
        ORDER BY created_at DESC
        """,
        (agent_id, cutoff_date.isoformat())
    ).fetchall()
    
    return [
        {
            "type": row[0],
            "amount": row[1],
            "description": row[2],
            "related_demand_id": row[3],
            "date": datetime.fromisoformat(row[4])
        }
        for row in rows
    ]


# Импортируем функцию расчета уровня в конце, чтобы избежать циклических импортов
from .loyalty import calculate_level_by_spent
from datetime import datetime, timedelta
