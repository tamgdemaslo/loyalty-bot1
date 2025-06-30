#!/usr/bin/env python3
"""
Скрипт для ретроспективной обработки истории ТО
Анализирует все отгрузки в МойСклад и обновляет историю техобслуживания
"""

import sqlite3
from datetime import datetime
from bot.moysklad import fetch_demand_full
from bot.maintenance import process_moysklad_services
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def process_all_maintenance_history():
    """Обрабатывает всю историю отгрузок для обновления данных ТО"""
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('loyalty.db')
    
    # Получаем всех клиентов
    clients = conn.execute("SELECT DISTINCT agent_id FROM bonuses").fetchall()
    
    for (agent_id,) in clients:
        try:
            log.info(f"Processing maintenance history for agent: {agent_id}")
            
            # Получаем все отгрузки для клиента
            try:
                from bot.moysklad import fetch_shipments
                shipments = fetch_shipments(agent_id, limit=100)  # Берем последние 100 отгрузок
                
                for shipment in shipments:
                    try:
                        # Получаем детали отгрузки
                        demand = fetch_demand_full(shipment["id"])
                        
                        # Извлекаем пробег
                        mileage = 0
                        attributes = demand.get('attributes', [])
                        for attr in attributes:
                            if attr.get('name') == 'Пробег':
                                mileage_str = str(attr.get('value', '0'))
                                mileage_clean = ''.join(filter(str.isdigit, mileage_str))
                                mileage = int(mileage_clean) if mileage_clean else 0
                                break
                        
                        if mileage == 0:
                            continue  # Пропускаем отгрузки без пробега
                        
                        # Извлекаем услуги
                        services = []
                        positions = demand.get("positions", {}).get("rows", [])
                        for p in positions:
                            if p["assortment"]["meta"]["type"] == "service":
                                services.append(p)
                        
                        if not services:
                            continue  # Пропускаем отгрузки без услуг
                        
                        # Получаем дату отгрузки
                        demand_date = datetime.fromisoformat(demand["moment"].replace("Z", "+00:00")).strftime("%Y-%m-%d")
                        
                        # Обрабатываем услуги для ТО
                        process_moysklad_services(agent_id, demand["id"], services, mileage, demand_date)
                        
                        log.info(f"Processed demand {demand['id']} with {len(services)} services, mileage: {mileage}")
                        
                    except Exception as e:
                        log.error(f"Error processing demand {shipment['id']}: {e}")
                        continue
                        
            except Exception as e:
                log.error(f"Error fetching shipments for agent {agent_id}: {e}")
                continue
                
        except Exception as e:
            log.error(f"Error processing agent {agent_id}: {e}")
            continue
    
    conn.close()
    log.info("Maintenance history processing completed!")

if __name__ == "__main__":
    print("🔧 Обработка истории технического обслуживания...")
    print("Это может занять несколько минут...")
    
    try:
        process_all_maintenance_history()
        print("✅ Обработка завершена успешно!")
        
        # Показываем статистику
        conn = sqlite3.connect('loyalty.db')
        count = conn.execute("SELECT COUNT(*) FROM maintenance_history").fetchone()[0]
        unique_agents = conn.execute("SELECT COUNT(DISTINCT agent_id) FROM maintenance_history").fetchone()[0]
        conn.close()
        
        print(f"📊 Статистика:")
        print(f"   • Записей ТО: {count}")
        print(f"   • Клиентов: {unique_agents}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
