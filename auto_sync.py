#!/usr/bin/env python3
"""
Скрипт для автоматической синхронизации данных из МойСклад
Запускается по расписанию и обновляет данные отгрузок
"""

import sys
import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.moysklad import _get
    from bot.config import HEADERS
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_sync.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def create_tables():
    """Создает таблицы для хранения данных контрагентов"""
    conn = sqlite3.connect("loyalty.db")
    
    # Таблица с детальными данными контрагентов
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contractors_data (
            agent_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица с отгрузками
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contractor_shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            demand_id TEXT UNIQUE,
            agent_id TEXT NOT NULL,
            name TEXT,
            moment TEXT,
            sum INTEGER DEFAULT 0,
            state_name TEXT DEFAULT '',
            positions_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES contractors_data(agent_id)
        )
    """)
    
    conn.commit()
    conn.close()


def get_recent_shipments(days_back: int = 7) -> List[Dict]:
    """
    Получает отгрузки за последние N дней
    """
    try:
        # Вычисляем дату начала
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "filter": f"moment>={start_date.strftime('%Y-%m-%d %H:%M:%S')};moment<={end_date.strftime('%Y-%m-%d %H:%M:%S')}",
            "order": "moment,desc", 
            "limit": 1000,
            "expand": "agent,state"
        }
        
        response = _get("entity/demand", params)
        demands = response.get('rows', [])
        
        shipments = []
        for demand in demands:
            agent = demand.get('agent', {})
            agent_id = agent.get('meta', {}).get('href', '').split('/')[-1] if agent else None
            
            if agent_id:
                shipments.append({
                    'demand_id': demand.get('id'),
                    'agent_id': agent_id,
                    'name': demand.get('name'),
                    'moment': demand.get('moment'),
                    'sum': demand.get('sum', 0),
                    'state_name': demand.get('state', {}).get('name', ''),
                    'positions_count': len(demand.get('positions', {}).get('rows', [])),
                    'created_at': datetime.now().isoformat()
                })
        
        return shipments
        
    except Exception as e:
        log.error(f"Ошибка получения отгрузок: {e}")
        return []


def get_contractor_details(agent_id: str) -> Optional[Dict]:
    """Получает детальную информацию о контрагенте по ID"""
    try:
        contractor = _get(f"entity/counterparty/{agent_id}")
        
        # Проверяем, что contractor не является строкой (ошибка)
        if isinstance(contractor, str):
            log.error(f"Получена строка вместо объекта для контрагента {agent_id}: {contractor}")
            return None
            
        name = contractor.get('name', 'Не указан')
        description = contractor.get('description', '')
        email = contractor.get('email', '')
        phone = contractor.get('phone', '')
        
        # Извлекаем адрес
        address = ''
        if contractor.get('actualAddress'):
            addr_parts = []
            addr = contractor['actualAddress']
            if addr.get('city'):
                addr_parts.append(addr['city'])
            if addr.get('street'):
                addr_parts.append(addr['street'])
            if addr.get('house'):
                addr_parts.append(f"д.{addr['house']}")
            address = ', '.join(addr_parts)
        
        return {
            'agent_id': agent_id,
            'name': name,
            'description': description,
            'email': email,
            'phone': phone,
            'address': address,
            'updated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        log.error(f"Ошибка получения данных контрагента {agent_id}: {e}")
        return None


def save_contractor_data(contractor_data: Dict):
    """Сохраняет данные контрагента в базу"""
    conn = sqlite3.connect("loyalty.db")
    
    conn.execute("""
        INSERT OR REPLACE INTO contractors_data 
        (agent_id, name, description, email, phone, address, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        contractor_data['agent_id'],
        contractor_data['name'],
        contractor_data['description'],
        contractor_data['email'],
        contractor_data['phone'],
        contractor_data['address'],
        contractor_data['updated_at']
    ))
    
    conn.commit()
    conn.close()


def save_shipments(shipments: List[Dict]):
    """Сохраняет отгрузки в базу"""
    if not shipments:
        return
        
    conn = sqlite3.connect("loyalty.db")
    
    saved_count = 0
    for shipment in shipments:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO contractor_shipments 
                (demand_id, agent_id, name, moment, sum, state_name, positions_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                shipment['demand_id'],
                shipment['agent_id'], 
                shipment['name'],
                shipment['moment'],
                shipment['sum'],
                shipment['state_name'],
                shipment['positions_count'],
                shipment['created_at']
            ))
            saved_count += 1
        except Exception as e:
            log.error(f"Ошибка сохранения отгрузки {shipment['demand_id']}: {e}")
    
    conn.commit()
    conn.close()
    
    log.info(f"Сохранено {saved_count} отгрузок")


def sync_recent_data(days_back: int = 7):
    """
    Синхронизирует данные за последние дни
    """
    log.info(f"Начинаем синхронизацию данных за последние {days_back} дней...")
    
    # Создаем таблицы если не существуют
    create_tables()
    
    # Получаем недавние отгрузки
    shipments = get_recent_shipments(days_back)
    log.info(f"Найдено {len(shipments)} отгрузок")
    
    if not shipments:
        log.info("Нет отгрузок для синхронизации")  
        return
    
    # Получаем уникальные agent_id из отгрузок
    agent_ids = list(set(s['agent_id'] for s in shipments))
    log.info(f"Найдено {len(agent_ids)} уникальных контрагентов")
    
    # Синхронизируем данные контрагентов
    for i, agent_id in enumerate(agent_ids, 1):
        try:
            contractor_data = get_contractor_details(agent_id)
            if contractor_data:
                save_contractor_data(contractor_data)
                log.info(f"[{i}/{len(agent_ids)}] Синхронизирован контрагент: {contractor_data['name']}")
            else:
                log.warning(f"[{i}/{len(agent_ids)}] Не удалось получить данные контрагента {agent_id}")
        except Exception as e:
            log.error(f"[{i}/{len(agent_ids)}] Ошибка синхронизации контрагента {agent_id}: {e}")
    
    # Сохраняем отгрузки
    save_shipments(shipments)
    
    log.info("Синхронизация завершена")


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Автоматическая синхронизация данных МойСклад')
    parser.add_argument('--days', type=int, default=7, help='Количество дней для синхронизации (по умолчанию: 7)')
    parser.add_argument('--full', action='store_true', help='Полная синхронизация всех контрагентов')
    
    args = parser.parse_args()
    
    try:
        if args.full:
            log.info("Запуск полной синхронизации...")
            # Импортируем и запускаем полную синхронизацию
            from sync_contractors_data import sync_all_contractors
            sync_all_contractors()
        else:
            sync_recent_data(args.days)
            
    except KeyboardInterrupt:
        log.info("Синхронизация прервана пользователем")
    except Exception as e:
        log.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
