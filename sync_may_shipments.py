#!/usr/bin/env python3
"""
Скрипт для синхронизации отгрузок за конкретный месяц
Обходит проблемы с лимитами и синхронизирует все отгрузки напрямую по дате
"""

import sys
import os
import sqlite3
from datetime import datetime

# Добавляем путь к модулям бота  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.moysklad import _get
    from bot.config import HEADERS
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    sys.exit(1)

def get_all_demands_for_month(year, month):
    """
    Получает ВСЕ отгрузки за указанный месяц напрямую из API
    """
    print(f"🔍 Получаем все отгрузки за {month:02d}.{year}...")
    
    # Формируем даты начала и конца месяца
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    start_date = f"{year}-{month:02d}-01 00:00:00"
    end_date = f"{next_year}-{next_month:02d}-01 00:00:00"
    
    all_demands = []
    offset = 0
    limit = 1000  # Максимальный лимит API МойСклад
    
    while True:
        try:
            params = {
                "filter": f"moment>={start_date};moment<{end_date}",
                "order": "moment,desc",
                "limit": limit,
                "offset": offset
            }
            
            response = _get("entity/demand", params)
            demands = response.get('rows', [])
            
            if not demands:
                break
                
            all_demands.extend(demands)
            print(f"  Загружено {len(all_demands)} отгрузок...")
            
            # Если получили меньше лимита, значит это все
            if len(demands) < limit:
                break
                
            offset += limit
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке: {e}")
            break
    
    print(f"✅ Всего загружено {len(all_demands)} отгрузок")
    return all_demands

def save_demand_to_db(demand):
    """
    Сохраняет отгрузку в базу данных
    """
    # Извлекаем agent_id из мета-информации
    agent = demand.get('agent', {})
    agent_meta = agent.get('meta', {})
    agent_href = agent_meta.get('href', '')
    agent_id = agent_href.split('/')[-1] if agent_href else None
    
    if not agent_id:
        return False
    
    conn = sqlite3.connect("loyalty.db")
    
    try:
        conn.execute("""
            INSERT OR REPLACE INTO contractor_shipments 
            (demand_id, agent_id, name, moment, sum, state_name, positions_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            demand.get('id'),
            agent_id,
            demand.get('name'),
            demand.get('moment'),
            demand.get('sum', 0),
            demand.get('state', {}).get('name', ''),
            0,  # positions_count - можно добавить позже если нужно
            datetime.now().isoformat()
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения отгрузки {demand.get('name')}: {e}")
        return False
        
    finally:
        conn.close()

def sync_month_shipments(year, month):
    """
    Синхронизирует все отгрузки за месяц
    """
    print(f"🔄 Синхронизация отгрузок за {month:02d}.{year}")
    print("=" * 50)
    
    # Получаем все отгрузки за месяц
    demands = get_all_demands_for_month(year, month)
    
    if not demands:
        print("❌ Не найдено отгрузок для синхронизации")
        return
    
    # Сохраняем в базу
    saved_count = 0
    failed_count = 0
    
    print("\n💾 Сохраняем отгрузки в базу данных...")
    
    for i, demand in enumerate(demands, 1):
        if i % 50 == 0:
            print(f"  Обработано {i}/{len(demands)} отгрузок...")
        
        if save_demand_to_db(demand):
            saved_count += 1
        else:
            failed_count += 1
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("ИТОГОВЫЙ ОТЧЕТ СИНХРОНИЗАЦИИ:")
    print("=" * 50)
    print(f"Всего отгрузок из API: {len(demands)}")
    print(f"Успешно сохранено: {saved_count}")
    print(f"Ошибок сохранения: {failed_count}")
    
    # Проверяем итоговые данные в базе
    conn = sqlite3.connect("loyalty.db")
    result = conn.execute("""
        SELECT COUNT(*) as count, SUM(sum)/100.0 as total_rubles 
        FROM contractor_shipments 
        WHERE strftime('%Y-%m', moment) = ?
    """, (f"{year}-{month:02d}",)).fetchone()
    conn.close()
    
    print(f"Отгрузок в базе за {month:02d}.{year}: {result[0]}")
    print(f"Общая сумма в базе: {result[1]:.2f} руб")
    print("=" * 50)

if __name__ == "__main__":
    print("🔄 Синхронизация отгрузок за конкретный месяц")
    print("Этот скрипт синхронизирует ВСЕ отгрузки за месяц, минуя лимиты по контрагентам")
    print()
    
    # Синхронизируем май 2025
    sync_month_shipments(2025, 5)
