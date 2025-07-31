#!/usr/bin/env python3
"""
Скрипт для выгрузки всех контрагентов из МойСклад и начисления бонусов
Начисляет 200 рублей (20000 копеек) каждому контрагенту
"""

import sys
import os
import logging
import csv
from datetime import datetime
from typing import List, Dict, Tuple

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.moysklad import _get
    from bot.db import change_balance, add_bonus_transaction
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что запускаете скрипт из директории проекта")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('moysklad_bonus_accrual.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def get_all_agents(limit_per_page: int = 1000) -> List[Dict]:
    """
    Получает всех контрагентов из МойСклад с пагинацией
    
    Args:
        limit_per_page: количество записей на страницу (макс 1000)
    
    Returns:
        List[Dict]: список всех контрагентов
    """
    log.info("Загружаем контрагентов из МойСклад...")
    agents = []
    offset = 0
    
    while True:
        try:
            response = _get("entity/counterparty", params={
                "offset": offset, 
                "limit": limit_per_page,
                "order": "name,asc"
            })
            
            rows = response.get('rows', [])
            if not rows:
                break
                
            agents.extend(rows)
            offset += len(rows)
            
            log.info(f"Загружено {len(agents)} контрагентов...")
            
            # Если получили меньше лимита, значит это последняя страница
            if len(rows) < limit_per_page:
                break
                
        except Exception as e:
            log.error(f"Ошибка при загрузке контрагентов (offset={offset}): {e}")
            break
    
    log.info(f"Всего загружено контрагентов: {len(agents)}")
    return agents


def display_agents_preview(agents: List[Dict], max_display: int = 10):
    """
    Отображает превью списка контрагентов
    """
    print("\n" + "="*100)
    print("СПИСОК КОНТРАГЕНТОВ ИЗ МОЙСКЛАД:")
    print("="*100)
    print(f"{'№':<3} {'Название':<50} {'ID':<40}")
    print("-"*100)
    
    for i, agent in enumerate(agents[:max_display], 1):
        name = agent.get('name', 'Без названия')[:49]
        agent_id = agent.get('id', 'Без ID')
        print(f"{i:<3} {name:<50} {agent_id}")
    
    if len(agents) > max_display:
        print(f"... и еще {len(agents) - max_display} контрагентов")
    
    print("-"*100)
    print(f"Всего контрагентов: {len(agents)}")
    print("="*100)


def bulk_accrue_bonuses(agents: List[Dict], amount: int = 20000) -> Tuple[int, int]:
    """
    Массовое начисление бонусов контрагентам из МойСклад
    
    Args:
        agents: список контрагентов
        amount: сумма начисления в копейках (по умолчанию 20000 = 200 руб)
    
    Returns:
        Tuple[int, int]: (успешные начисления, неудачные начисления)
    """
    log.info("Начинаем массовое начисление бонусов...")
    
    if not agents:
        log.warning("Список контрагентов пуст")
        return 0, 0

    successful_accruals = 0
    failed_accruals = 0
    description = f"Массовое начисление бонусов из МойСklad {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    print(f"\nНачинаем начисление {amount/100:.2f} руб каждому из {len(agents)} контрагентов...")
    
    for i, agent in enumerate(agents, 1):
        agent_id = agent.get('id')
        name = agent.get('name', 'Без названия')
        
        if not agent_id:
            log.error(f"Контрагент без ID: {agent}")
            failed_accruals += 1
            continue
        
        print(f"[{i}/{len(agents)}] {name[:50]}...", end="")
        
        try:
            change_balance(agent_id, amount)
            add_bonus_transaction(agent_id, "accrual", amount, description)
            print(f" ✓ (+{amount/100:.2f} руб)")
            log.info(f"Успешно начислено {amount/100:.2f} руб для {name} ({agent_id})")
            successful_accruals += 1
        except Exception as e:
            print(f" ✗ ОШИБКА: {e}")
            log.error(f"Ошибка начисления для {name} ({agent_id}): {e}")
            failed_accruals += 1
    
    return successful_accruals, failed_accruals


def export_agents_to_csv(agents: List[Dict]) -> str:
    """
    Экспортирует список контрагентов в CSV файл
    
    Args:
        agents: список контрагентов
    
    Returns:
        str: имя созданного файла
    """
    filename = f"moysklad_agents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Заголовки
        writer.writerow(['ID', 'Название', 'Описание', 'Email', 'Телефон', 'Тип'])
        
        # Данные
        for agent in agents:
            writer.writerow([
                agent.get('id', ''),
                agent.get('name', ''),
                agent.get('description', ''),
                agent.get('email', ''),
                agent.get('phone', ''),
                agent.get('companyType', '')
            ])
    
    log.info(f"Экспорт контрагентов завершен: {filename}")
    return filename


def print_final_report(total_agents: int, successful: int, failed: int, amount: int):
    """
    Выводит итоговый отчет
    """
    print("\n" + "="*80)
    print("ИТОГОВЫЙ ОТЧЕТ НАЧИСЛЕНИЯ БОНУСОВ")
    print("="*80)
    print(f"Всего контрагентов в МойСклад: {total_agents}")
    print(f"Успешных начислений: {successful}")
    print(f"Неудачных начислений: {failed}")
    print(f"Сумма начисления на одного: {amount/100:.2f} руб")
    print(f"Общая сумма начислений: {successful * amount/100:.2f} руб")
    print(f"Дата операции: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("="*80)
    
    log.info(f"Массовое начисление завершено. Успешно: {successful}, Ошибок: {failed}")


def main():
    """
    Главная функция
    """
    print("🏪 Скрипт начисления бонусов контрагентам из МойСклад")
    print("📊 Загружаем данные...")
    
    try:
        # Получаем всех контрагентов
        agents = get_all_agents()
        
        if not agents:
            print("❌ Контрагенты не найдены в МойСклад")
            return
        
        # Показываем превью
        display_agents_preview(agents)
        
        # Запрашиваем подтверждение
        print(f"\n💰 Будет начислено по 200.00 рублей каждому контрагенту")
        print(f"💸 Общая сумма начислений: {len(agents) * 200:.2f} рублей")
        
        choice = input("\n❓ Продолжить начисление? (y/N): ").strip().lower()
        
        if choice != 'y':
            print("❌ Операция отменена пользователем")
            
            # Предлагаем экспорт
            export_choice = input("💾 Экспортировать список контрагентов в CSV? (y/N): ").strip().lower()
            if export_choice == 'y':
                filename = export_agents_to_csv(agents)
                print(f"✅ Данные экспортированы в файл: {filename}")
            
            return
        
        # Выполняем начисление
        successful, failed = bulk_accrue_bonuses(agents, 20000)  # 200 рублей
        
        # Выводим итоговый отчет
        print_final_report(len(agents), successful, failed, 20000)
        
        # Экспортируем данные
        filename = export_agents_to_csv(agents)
        print(f"\n💾 Список контрагентов сохранен: {filename}")
        
    except KeyboardInterrupt:
        print("\n❌ Операция прервана пользователем")
    except Exception as e:
        log.error(f"Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")
        print("🔍 Подробности в файле moysklad_bonus_accrual.log")


if __name__ == "__main__":
    main()
