#!/usr/bin/env python3
"""
Скрипт для тестирования API МойСклад и анализа расхождений в данных
"""

import sys
import os
from datetime import datetime

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.moysklad import _get
    from bot.config import HEADERS
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    sys.exit(1)

def test_demands_for_may():
    """
    Получает все отгрузки за май 2025 без фильтрации по агентам
    """
    print("🔍 Получаем все отгрузки за май 2025...")
    
    try:
        params = {
            "filter": "moment>=2025-05-01 00:00:00;moment<2025-06-01 00:00:00",
            "order": "moment,desc",
            "limit": 1000
        }
        
        response = _get("entity/demand", params)
        demands = response.get('rows', [])
        
        print(f"📊 Найдено отгрузок: {len(demands)}")
        print(f"📊 Общее количество: {response.get('meta', {}).get('size', 'неизвестно')}")
        
        # Подсчитываем суммы
        total_sum = sum(demand.get('sum', 0) for demand in demands)
        print(f"💰 Общая сумма: {total_sum/100:.2f} руб")
        
        # Показываем первые 5 записей
        print("\n📋 Первые 5 отгрузок:")
        for i, demand in enumerate(demands[:5]):
            print(f"  {i+1}. {demand.get('name')} - {demand.get('sum', 0)/100:.2f} руб - {demand.get('moment')}")
            
        return demands
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def test_sales_for_may():
    """
    Получает все продажи (sales) за май 2025
    """
    print("\n🔍 Получаем все продажи (sales) за май 2025...")
    
    try:
        params = {
            "filter": "moment>=2025-05-01 00:00:00;moment<2025-06-01 00:00:00",
            "order": "moment,desc", 
            "limit": 1000
        }
        
        response = _get("entity/customerorder", params)
        orders = response.get('rows', [])
        
        print(f"📊 Найдено заказов покупателей: {len(orders)}")
        
        # Подсчитываем суммы
        total_sum = sum(order.get('sum', 0) for order in orders)
        print(f"💰 Общая сумма: {total_sum/100:.2f} руб")
        
        return orders
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def analyze_agents_in_demands(demands):
    """
    Анализирует агентов в отгрузках
    """
    print("\n🔍 Анализируем контрагентов в отгрузках...")
    
    agents = {}
    for demand in demands:
        agent = demand.get('agent', {})
        agent_id = agent.get('meta', {}).get('href', '').split('/')[-1] if agent.get('meta') else None
        agent_name = agent.get('name', 'Неизвестен')
        
        if agent_id:
            if agent_id not in agents:
                agents[agent_id] = {
                    'name': agent_name,
                    'count': 0,
                    'sum': 0
                }
            agents[agent_id]['count'] += 1
            agents[agent_id]['sum'] += demand.get('sum', 0)
    
    print(f"📊 Уникальных контрагентов: {len(agents)}")
    
    # Топ-10 по количеству отгрузок
    top_agents = sorted(agents.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
    print("\n🏆 Топ-10 контрагентов по количеству отгрузок:")
    for agent_id, data in top_agents:
        print(f"  {data['name'][:30]}: {data['count']} отгрузок, {data['sum']/100:.2f} руб")
    
    return agents

if __name__ == "__main__":
    print("🧪 Тестирование API МойСклад для анализа расхождений")
    print("=" * 60)
    
    # Получаем отгрузки
    demands = test_demands_for_may()
    
    if demands:
        # Анализируем агентов
        agents = analyze_agents_in_demands(demands)
        
        print(f"\n📋 Итого:")
        print(f"  Отгрузок в API: {len(demands)}")
        print(f"  Уникальных контрагентов: {len(agents)}")
        
    # Также проверим заказы покупателей
    test_sales_for_may()
