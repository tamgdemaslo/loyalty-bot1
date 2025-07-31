#!/usr/bin/env python3
"""
Скрипт для синхронизации данных контрагентов из МойСклад
Загружает имена, телефоны и данные отгрузок для всех контрагентов
"""

import sys
import os
import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.moysklad import _get
    from bot.config import HEADERS
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что запускаете скрипт из директории проекта")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_contractors.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def get_contractor_details(agent_id: str) -> Optional[Dict]:
    """
    Получает детальную информацию о контрагенте по ID
    """
    try:
        contractor = _get(f"entity/counterparty/{agent_id}")
        
        # Извлекаем нужные данные
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


def get_contractor_shipments(agent_id: str, limit: int = 1000) -> List[Dict]:
    """
    Получает список отгрузок для контрагента
    """
    try:
        params = {
            "filter": f"agent=https://api.moysklad.ru/api/remap/1.2/entity/counterparty/{agent_id}",
            "order": "moment,desc",
            "limit": limit,
            "expand": "positions,positions.assortment,state"
        }
        
        response = _get("entity/demand", params)
        demands = response.get('rows', [])
        
        shipments = []
        for demand in demands:
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
        log.error(f"Ошибка получения отгрузок для {agent_id}: {e}")
        return []


def create_tables():
    """
    Создает таблицы для хранения данных контрагентов
    """
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


def save_contractor_data(contractor_data: Dict):
    """
    Сохраняет данные контрагента в базу
    """
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
    """
    Сохраняет отгрузки в базу
    """
    if not shipments:
        return
        
    conn = sqlite3.connect("loyalty.db")
    
    for shipment in shipments:
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
    
    conn.commit()
    conn.close()


def get_all_contractor_ids() -> List[str]:
    """
    Получает список всех ID контрагентов с бонусами
    """
    conn = sqlite3.connect("loyalty.db")
    
    cursor = conn.execute("SELECT agent_id FROM bonuses")
    agent_ids = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return agent_ids


def sync_all_contractors():
    """
    Синхронизирует данные всех контрагентов
    """
    log.info("Начинаем синхронизацию данных контрагентов...")
    
    # Создаем таблицы
    create_tables()
    
    # Получаем все ID контрагентов
    agent_ids = get_all_contractor_ids()
    log.info(f"Найдено {len(agent_ids)} контрагентов для синхронизации")
    
    successful_sync = 0
    failed_sync = 0
    
    for i, agent_id in enumerate(agent_ids, 1):
        print(f"[{i}/{len(agent_ids)}] Синхронизация {agent_id[:8]}...", end="")
        
        try:
            # Получаем данные контрагента
            contractor_data = get_contractor_details(agent_id)
            
            if contractor_data:
                # Сохраняем данные контрагента
                save_contractor_data(contractor_data)
                
                # Получаем отгрузки
                shipments = get_contractor_shipments(agent_id)
                save_shipments(shipments)
                
                print(f" ✓ (имя: {contractor_data['name'][:30]}, отгрузок: {len(shipments)})")
                log.info(f"Синхронизирован {agent_id}: {contractor_data['name']}, {len(shipments)} отгрузок")
                successful_sync += 1
            else:
                print(f" ✗ Ошибка получения данных")
                failed_sync += 1
                
        except Exception as e:
            print(f" ✗ Ошибка: {e}")
            log.error(f"Ошибка синхронизации {agent_id}: {e}")
            failed_sync += 1
    
    # Итоговый отчет
    print("\n" + "="*80)
    print("ИТОГОВЫЙ ОТЧЕТ СИНХРОНИЗАЦИИ:")
    print("="*80)
    print(f"Всего контрагентов: {len(agent_ids)}")
    print(f"Успешно синхронизировано: {successful_sync}")
    print(f"Ошибок синхронизации: {failed_sync}")
    print(f"Дата синхронизации: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("="*80)
    
    log.info(f"Синхронизация завершена. Успешно: {successful_sync}, Ошибок: {failed_sync}")


def export_contractors_with_data():
    """
    Экспортирует контрагентов с полными данными в CSV
    """
    conn = sqlite3.connect("loyalty.db")
    
    query = """
        SELECT 
            b.agent_id,
            cd.name,
            cd.phone,
            cd.email,
            cd.address,
            b.balance,
            COUNT(cs.demand_id) as shipments_count,
            SUM(cs.sum) as total_shipments_sum
        FROM bonuses b
        LEFT JOIN contractors_data cd ON b.agent_id = cd.agent_id
        LEFT JOIN contractor_shipments cs ON b.agent_id = cs.agent_id
        GROUP BY b.agent_id, cd.name, cd.phone, cd.email, cd.address, b.balance
        ORDER BY b.balance DESC
    """
    
    contractors = conn.execute(query).fetchall()
    conn.close()
    
    if not contractors:
        print("Нет данных для экспорта")
        return
    
    filename = f"contractors_full_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    import csv
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Заголовки
        writer.writerow([
            'Agent ID', 'Название', 'Телефон', 'Email', 'Адрес', 
            'Баланс (руб)', 'Количество отгрузок', 'Сумма отгрузок (коп)'
        ])
        
        # Данные
        for row in contractors:
            writer.writerow([
                row[0],  # agent_id
                row[1] or 'Не указан',  # name
                row[2] or 'Не указан',  # phone
                row[3] or 'Не указан',  # email
                row[4] or 'Не указан',  # address
                (row[5] or 0) / 100,  # balance in rubles
                row[6] or 0,  # shipments_count
                row[7] or 0  # total_shipments_sum
            ])
    
    print(f"✅ Данные экспортированы в файл: {filename}")
    print(f"📊 Экспортировано {len(contractors)} контрагентов")


def main():
    """
    Главная функция
    """
    print("🔄 Синхронизация данных контрагентов из МойСклад")
    print("1. Синхронизировать все данные контрагентов")
    print("2. Экспортировать данные в CSV")
    print("3. Показать статистику синхронизации")
    
    choice = input("\nВыберите действие (1-3): ").strip()
    
    if choice == "1":
        sync_all_contractors()
    elif choice == "2":
        export_contractors_with_data()
    elif choice == "3":
        # Показываем статистику
        conn = sqlite3.connect("loyalty.db")
        
        stats = {}
        stats['contractors'] = conn.execute("SELECT COUNT(*) FROM contractors_data").fetchone()[0]
        stats['shipments'] = conn.execute("SELECT COUNT(*) FROM contractor_shipments").fetchone()[0]
        stats['with_phone'] = conn.execute("SELECT COUNT(*) FROM contractors_data WHERE phone != ''").fetchone()[0]
        stats['with_email'] = conn.execute("SELECT COUNT(*) FROM contractors_data WHERE email != ''").fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 Статистика синхронизации:")
        print(f"- Контрагентов в базе: {stats['contractors']}")
        print(f"- Отгрузок в базе: {stats['shipments']}")
        print(f"- С указанным телефоном: {stats['with_phone']}")
        print(f"- С указанным email: {stats['with_email']}")
    else:
        print("Неверный выбор")


if __name__ == "__main__":
    main()
