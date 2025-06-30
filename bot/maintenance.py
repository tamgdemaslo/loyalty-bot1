# loyalty-bot/bot/maintenance.py
"""
Модуль технического обслуживания (ТО)
Управление регламентными работами и их отслеживание
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .db_postgres import conn
from .formatting import fmt_date_local

# Справочник регламентных работ ТО
MAINTENANCE_WORKS = {
    1: {
        "name": "Замена моторного масла в двигателе и масляного фильтра",
        "category": "Двигатель",
        "mileage_interval": 7000,  # км
        "time_interval": 6,  # месяцев
        "priority": 1,  # приоритет (1 - самый высокий)
        "emoji": "🛢️",
        "description": "Замена моторного масла и фильтра для защиты двигателя"
    },
    2: {
        "name": "Работа по частичной замене трансмиссионного масла",
        "category": "Коробка",
        "mileage_interval": 25000,
        "time_interval": 24,
        "priority": 2,
        "emoji": "⚙️",
        "description": "Частичная замена масла в трансмиссии"
    },
    3: {
        "name": "Работа по аппаратной замене масла в АКПП",
        "category": "Коробка",
        "mileage_interval": 60000,
        "time_interval": 36,
        "priority": 3,
        "emoji": "🔧",
        "description": "Полная аппаратная замена масла в автоматической КПП"
    },
    4: {
        "name": "Аппаратная замена тормозной жидкости",
        "category": "Тормоза",
        "mileage_interval": 40000,
        "time_interval": 24,
        "priority": 2,
        "emoji": "🛑",
        "description": "Замена тормозной жидкости для безопасности"
    },
    5: {
        "name": "Замена воздушного фильтра",
        "category": "Двигатель",
        "mileage_interval": 7000,
        "time_interval": 6,
        "priority": 2,
        "emoji": "💨",
        "description": "Замена воздушного фильтра двигателя"
    },
    6: {
        "name": "Замена салонного фильтра",
        "category": "Салон",
        "mileage_interval": 7000,
        "time_interval": 12,
        "priority": 3,
        "emoji": "🌬️",
        "description": "Замена фильтра салона для чистого воздуха"
    },
    7: {
        "name": "Замена топливного фильтра (не в баке)",
        "category": "Топливная система",
        "mileage_interval": 20000,
        "time_interval": 12,
        "priority": 2,
        "emoji": "⛽",
        "description": "Замена топливного фильтра для чистого топлива"
    }
}

# Соответствие услуг МойСклад и работ ТО
MOYSKLAD_SERVICE_MAPPING = {
    # Здесь будут ID услуг из МойСклад, которые соответствуют работам ТО
    # Пример: "service_id_from_moysklad": work_id_from_MAINTENANCE_WORKS
    # Эта таблица будет настраиваться администратором
}


def init_maintenance_tables():
    """Инициализация таблиц для модуля ТО"""
    try:
        cursor = conn.cursor()
        
        # Таблица истории выполненных работ ТО
        cursor.execute("""
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
        )
        """)
        
        # Таблица настроек ТО для клиентов (персональные интервалы)
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
        
        # Таблица соответствия услуг МойСклад и работ ТО
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_service_mapping (
            moysklad_service_name TEXT PRIMARY KEY,
            work_id INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
        """)
        
        # Индексы для быстрого поиска
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_maintenance_history_agent_work 
            ON maintenance_history(agent_id, work_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_maintenance_history_date 
            ON maintenance_history(performed_date)
        """)
        
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Ошибка при инициализации таблиц ТО: {e}")
        conn.rollback()


def get_work_info(work_id: int) -> Dict:
    """Получает информацию о работе ТО"""
    return MAINTENANCE_WORKS.get(work_id, {})


def get_work_intervals(agent_id: str, work_id: int) -> Tuple[int, int]:
    """
    Получает интервалы для работы ТО (пробег в км, время в месяцах)
    Учитывает персональные настройки клиента
    """
    # Проверяем персональные настройки
    cursor = conn.cursor()
    cursor.execute(
        "SELECT custom_mileage_interval, custom_time_interval FROM maintenance_settings WHERE agent_id = %s AND work_id = %s",
        (agent_id, work_id)
    )
    custom_settings = cursor.fetchone()
    
    if custom_settings and (custom_settings[0] or custom_settings[1]):
        mileage_interval = custom_settings[0] or MAINTENANCE_WORKS[work_id]["mileage_interval"]
        time_interval = custom_settings[1] or MAINTENANCE_WORKS[work_id]["time_interval"]
        return mileage_interval, time_interval
    
    # Используем стандартные интервалы
    work_info = MAINTENANCE_WORKS[work_id]
    return work_info["mileage_interval"], work_info["time_interval"]


def get_last_maintenance(agent_id: str, work_id: int) -> Optional[Dict]:
    """Получает информацию о последнем выполнении работы ТО"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT performed_date, mileage, source, notes, created_at
        FROM maintenance_history 
        WHERE agent_id = %s AND work_id = %s
        ORDER BY performed_date DESC, created_at DESC
        LIMIT 1
    """, (agent_id, work_id))
    row = cursor.fetchone()
    
    if not row:
        return None
    
    return {
        "date": datetime.fromisoformat(row[0]),
        "mileage": row[1],
        "source": row[2],
        "notes": row[3] or "",
        "created_at": datetime.fromisoformat(row[4])
    }


def get_current_mileage(agent_id: str) -> int:
    """Получает текущий пробег клиента из последней отгрузки"""
    from .moysklad import fetch_shipments
    
    shipments = fetch_shipments(agent_id, limit=1)
    if not shipments:
        return 0
    
    try:
        from .moysklad import fetch_demand_full
        demand = fetch_demand_full(shipments[0]["id"])
        
        # Извлекаем пробег из атрибутов
        attributes = demand.get('attributes', [])
        for attr in attributes:
            if attr.get('name') == 'Пробег':
                mileage_str = str(attr.get('value', '0'))
                # Очищаем от нечисловых символов
                mileage_clean = ''.join(filter(str.isdigit, mileage_str))
                return int(mileage_clean) if mileage_clean else 0
    except Exception:
        pass
    
    return 0


def calculate_maintenance_status(agent_id: str, work_id: int) -> Dict:
    """
    Рассчитывает статус работы ТО:
    - когда была выполнена последний раз
    - когда нужно выполнить следующий раз
    - сколько осталось (пробег/время)
    - статус (ОК, Скоро, Просрочено)
    """
    work_info = get_work_info(work_id)
    if not work_info:
        return {"status": "error", "message": "Работа не найдена"}
    
    # Получаем интервалы
    mileage_interval, time_interval = get_work_intervals(agent_id, work_id)
    
    # Получаем последнее выполнение
    last_maintenance = get_last_maintenance(agent_id, work_id)
    
    # Получаем текущий пробег
    current_mileage = get_current_mileage(agent_id)
    
    # Если работа никогда не выполнялась
    if not last_maintenance:
        return {
            "status": "never_done",
            "work_info": work_info,
            "current_mileage": current_mileage,
            "mileage_interval": mileage_interval,
            "time_interval": time_interval,
            "message": "Работа никогда не выполнялась",
            "priority": "high"
        }
    
    # Рассчитываем следующее обслуживание
    last_date = last_maintenance["date"]
    last_mileage = last_maintenance["mileage"]
    
    # По пробегу
    next_mileage = last_mileage + mileage_interval
    mileage_remaining = next_mileage - current_mileage
    
    # По времени
    next_date = last_date + timedelta(days=time_interval * 30)  # приблизительно
    days_remaining = (next_date - datetime.now()).days
    
    # Определяем статус
    mileage_overdue = mileage_remaining <= 0
    time_overdue = days_remaining <= 0
    
    mileage_soon = mileage_remaining <= (mileage_interval * 0.1)  # 10% от интервала
    time_soon = days_remaining <= 30  # месяц
    
    if mileage_overdue or time_overdue:
        status = "overdue"
        priority = "critical"
        if mileage_overdue and time_overdue:
            message = f"Просрочено на {abs(mileage_remaining)} км и {abs(days_remaining)} дней"
        elif mileage_overdue:
            message = f"Просрочено на {abs(mileage_remaining)} км"
        else:
            message = f"Просрочено на {abs(days_remaining)} дней"
    elif mileage_soon or time_soon:
        status = "soon"
        priority = "high"
        if mileage_soon and time_soon:
            message = f"Скоро: осталось {mileage_remaining} км или {days_remaining} дней"
        elif mileage_soon:
            message = f"Скоро: осталось {mileage_remaining} км"
        else:
            message = f"Скоро: осталось {days_remaining} дней"
    else:
        status = "ok"
        priority = "normal"
        message = f"В порядке: осталось {mileage_remaining} км или {days_remaining} дней"
    
    return {
        "status": status,
        "priority": priority,
        "work_info": work_info,
        "last_maintenance": last_maintenance,
        "current_mileage": current_mileage,
        "next_mileage": next_mileage,
        "next_date": next_date,
        "mileage_remaining": mileage_remaining,
        "days_remaining": days_remaining,
        "mileage_interval": mileage_interval,
        "time_interval": time_interval,
        "message": message
    }


def get_all_maintenance_status(agent_id: str) -> List[Dict]:
    """Получает статус всех работ ТО для клиента"""
    statuses = []
    
    for work_id in MAINTENANCE_WORKS.keys():
        status = calculate_maintenance_status(agent_id, work_id)
        status["work_id"] = work_id
        statuses.append(status)
    
    # Сортируем по приоритету: критичные, высокие, обычные
    priority_order = {"critical": 0, "high": 1, "normal": 2}
    statuses.sort(key=lambda x: (
        priority_order.get(x.get("priority", "normal"), 2),
        x["work_info"]["priority"]
    ))
    
    return statuses


def add_manual_maintenance(agent_id: str, work_id: int, date: str, mileage: int, notes: str = "") -> bool:
    """Добавляет ручную запись о выполненной работе ТО"""
    try:
        # Валидация данных
        if work_id not in MAINTENANCE_WORKS:
            return False
        
        # Проверяем формат даты
        try:
            datetime.fromisoformat(date)
        except ValueError:
            return False
        
        if mileage < 0:
            return False
        
        # Добавляем запись
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_history (agent_id, work_id, performed_date, mileage, source, notes)
            VALUES (%s, %s, %s, %s, 'manual', %s)
        """, (agent_id, work_id, date, mileage, notes))
        conn.commit()
        
        return True
    except Exception:
        return False


def add_auto_maintenance(agent_id: str, work_id: int, demand_id: str, date: str, mileage: int) -> bool:
    """Добавляет автоматическую запись о выполненной работе ТО (из МойСклад)"""
    try:
        # Проверяем, не добавлена ли уже запись для этой отгрузки
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM maintenance_history WHERE demand_id = %s AND work_id = %s",
            (demand_id, work_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            return False  # Уже добавлено
        
        cursor.execute("""
            INSERT INTO maintenance_history (agent_id, work_id, performed_date, mileage, source, demand_id)
            VALUES (%s, %s, %s, %s, 'auto', %s)
        """, (agent_id, work_id, date, mileage, demand_id))
        conn.commit()
        
        return True
    except Exception:
        return False


def process_moysklad_services(agent_id: str, demand_id: str, services: List[Dict], mileage: int, date: str):
    """Обрабатывает услуги из МойСклад и автоматически добавляет записи ТО"""
    for service in services:
        service_name = service.get("assortment", {}).get("name", "")
        
        # Ищем соответствие в настройках
        cursor = conn.cursor()
        cursor.execute(
            "SELECT work_id FROM maintenance_service_mapping WHERE moysklad_service_name = %s AND is_active = TRUE",
            (service_name,)
        )
        mapping = cursor.fetchone()
        
        if mapping:
            work_id = mapping[0]
            add_auto_maintenance(agent_id, work_id, demand_id, date, mileage)


def format_maintenance_status(status: Dict) -> str:
    """Форматирует статус работы ТО для отображения"""
    work_info = status["work_info"]
    
    # Определяем иконку статуса
    if status["status"] == "overdue":
        status_icon = "🔴"
    elif status["status"] == "soon":
        status_icon = "🟡"
    elif status["status"] == "never_done":
        status_icon = "⚪"
    else:
        status_icon = "🟢"
    
    # Базовая информация
    text = f"{status_icon} {work_info['emoji']} <b>{work_info['name']}</b>\n"
    text += f"📁 <i>{work_info['category']}</i>\n"
    
    if status["status"] == "never_done":
        text += f"❗ {status['message']}\n"
        text += f"📏 Регламент: {status['mileage_interval']:,} км / {status['time_interval']} мес\n"
    else:
        last = status["last_maintenance"]
        text += f"📅 Последний раз: {fmt_date_local(last['date'].isoformat())}\n"
        text += f"🛣️ При пробеге: {last['mileage']:,} км\n"
        
        if status["status"] == "overdue":
            text += f"⚠️ <b>{status['message']}</b>\n"
        elif status["status"] == "soon":
            text += f"⏰ <b>{status['message']}</b>\n"
        else:
            text += f"✅ <b>{status['message']}</b>\n"
        
        # Источник данных
        if last["source"] == "manual":
            text += f"✋ Добавлено вручную"
        else:
            text += f"🔄 Выполнено в сервисе"
        
        if last["notes"]:
            text += f"\n📝 {last['notes']}"
    
    return text


def format_maintenance_summary(statuses: List[Dict]) -> str:
    """Форматирует сводку по всем работам ТО"""
    overdue_count = sum(1 for s in statuses if s["status"] == "overdue")
    soon_count = sum(1 for s in statuses if s["status"] == "soon")
    never_done_count = sum(1 for s in statuses if s["status"] == "never_done")
    ok_count = sum(1 for s in statuses if s["status"] == "ok")
    
    text = "🔧 <b>Техническое обслуживание</b>\n\n"
    
    if overdue_count > 0:
        text += f"🔴 <b>Просрочено:</b> {overdue_count}\n"
    if soon_count > 0:
        text += f"🟡 <b>Скоро нужно:</b> {soon_count}\n"
    if never_done_count > 0:
        text += f"⚪ <b>Никогда не делали:</b> {never_done_count}\n"
    if ok_count > 0:
        text += f"🟢 <b>В порядке:</b> {ok_count}\n"
    
    text += f"\n📊 <b>Всего работ:</b> {len(statuses)}\n"
    
    # Показываем самые критичные
    critical_works = [s for s in statuses if s.get("priority") == "critical"][:3]
    if critical_works:
        text += "\n🚨 <b>Требует внимания:</b>\n"
        for work in critical_works:
            text += f"• {work['work_info']['emoji']} {work['work_info']['name'][:30]}...\n"
    
    return text


# Инициализируем таблицы при импорте модуля
init_maintenance_tables()
