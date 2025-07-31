#!/usr/bin/env python3
"""
Универсальный скрипт для синхронизации всех отгрузок за все месяцы
Обходит проблемы с лимитами и синхронизирует все отгрузки напрямую по дате
"""

import sys
import os
import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

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
    print(f"\n🔄 Синхронизация отгрузок за {month:02d}.{year}")
    print("=" * 50)
    
    # Получаем все отгрузки за месяц
    demands = get_all_demands_for_month(year, month)
    
    if not demands:
        print("❌ Не найдено отгрузок для синхронизации")
        return 0, 0
    
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
    
    # Проверяем итоговые данные в базе
    conn = sqlite3.connect("loyalty.db")
    result = conn.execute("""
        SELECT COUNT(*) as count, SUM(sum)/100.0 as total_rubles 
        FROM contractor_shipments 
        WHERE strftime('%Y-%m', moment) = ?
    """, (f"{year}-{month:02d}",)).fetchone()
    conn.close()
    
    print(f"\n✅ {month:02d}.{year}: {result[0]} отгрузок, {result[1]:.2f} руб")
    return saved_count, failed_count

def get_months_with_shipments():
    """
    Получает все месяцы, в которых есть отгрузки в базе
    """
    conn = sqlite3.connect("loyalty.db")
    months = conn.execute("""
        SELECT DISTINCT strftime('%Y-%m', moment) as month
        FROM contractor_shipments 
        WHERE moment IS NOT NULL
        ORDER BY month DESC
    """).fetchall()
    conn.close()
    
    return [month[0] for month in months]

def sync_all_months():
    """
    Синхронизирует все месяцы с отгрузками
    """
    print("🔄 ПОЛНАЯ СИНХРОНИЗАЦИЯ ВСЕХ ОТГРУЗОК")
    print("=" * 80)
    print("Этот скрипт пересинхронизирует ВСЕ отгрузки за все месяцы,")
    print("минуя лимиты по контрагентам и загружая данные напрямую по дате")
    print("=" * 80)
    
    # Получаем все месяцы с отгрузками
    months = get_months_with_shipments()
    print(f"\nНайдено {len(months)} месяцев с отгрузками:")
    for month in months[:10]:  # Показываем первые 10
        print(f"  • {month}")
    if len(months) > 10:
        print(f"  ... и еще {len(months) - 10} месяцев")
    
    # Подтверждение
    response = input(f"\nПродолжить синхронизацию всех {len(months)} месяцев? (y/N): ")
    if response.lower() != 'y':
        print("Синхронизация отменена")
        return
    
    # Синхронизируем все месяцы
    total_saved = 0
    total_failed = 0
    
    for month_str in months:
        year, month = map(int, month_str.split('-'))
        saved, failed = sync_month_shipments(year, month)
        total_saved += saved
        total_failed += failed
    
    # Итоговый отчет
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ ПОЛНОЙ СИНХРОНИЗАЦИИ:")
    print("=" * 80)
    print(f"Обработано месяцев: {len(months)}")
    print(f"Всего сохранено отгрузок: {total_saved}")
    print(f"Ошибок сохранения: {total_failed}")
    
    # Общая статистика по базе
    conn = sqlite3.connect("loyalty.db")
    total_result = conn.execute("""
        SELECT 
            COUNT(*) as total_count,
            SUM(sum)/100.0 as total_revenue,
            MIN(moment) as earliest_date,
            MAX(moment) as latest_date
        FROM contractor_shipments 
        WHERE moment IS NOT NULL
    """).fetchone()
    conn.close()
    
    print(f"\nОБЩАЯ СТАТИСТИКА БАЗЫ ДАННЫХ:")
    print(f"Всего отгрузок в базе: {total_result[0]}")
    print(f"Общая выручка: {total_result[1]:.2f} руб")
    print(f"Период: {total_result[2][:10]} - {total_result[3][:10]}")
    print("=" * 80)

def sync_recent_months(months_count=6):
    """
    Синхронизирует только последние N месяцев
    """
    print(f"🔄 СИНХРОНИЗАЦИЯ ПОСЛЕДНИХ {months_count} МЕСЯЦЕВ")
    print("=" * 60)
    
    # Вычисляем последние месяцы
    current_date = date.today()
    months_to_sync = []
    
    for i in range(months_count):
        month_date = current_date - relativedelta(months=i)
        months_to_sync.append((month_date.year, month_date.month))
    
    months_to_sync.reverse()  # От старых к новым
    
    print("Будут синхронизированы месяцы:")
    for year, month in months_to_sync:
        print(f"  • {month:02d}.{year}")
    
    # Синхронизируем
    total_saved = 0
    total_failed = 0
    
    for year, month in months_to_sync:
        saved, failed = sync_month_shipments(year, month)
        total_saved += saved
        total_failed += failed
    
    print(f"\n✅ Синхронизация завершена!")
    print(f"Всего сохранено: {total_saved}, ошибок: {total_failed}")

if __name__ == "__main__":
    print("🔄 УНИВЕРСАЛЬНЫЙ СИНХРОНИЗАТОР ОТГРУЗОК")
    print("=" * 50)
    print("Выберите режим работы:")
    print("1. Синхронизация всех месяцев (полная)")
    print("2. Синхронизация последних 6 месяцев")
    print("3. Синхронизация последних 12 месяцев")
    print("4. Синхронизация конкретного месяца")
    print("=" * 50)
    
    choice = input("Ваш выбор (1-4): ").strip()
    
    if choice == "1":
        sync_all_months()
    elif choice == "2":
        sync_recent_months(6)
    elif choice == "3":
        sync_recent_months(12)
    elif choice == "4":
        year = int(input("Введите год (например, 2025): "))
        month = int(input("Введите месяц (1-12): "))
        sync_month_shipments(year, month)
    else:
        print("Неверный выбор!")
