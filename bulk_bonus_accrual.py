#!/usr/bin/env python3
"""
Скрипт для массового начисления бонусов всем контрагентам
Начисляет 200 рублей (20000 копеек) каждому контрагенту
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_bonus_accrual.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

def get_all_contractors() -> List[Tuple[str, str, str, int]]:
    """
    Получает всех контрагентов из базы данных
    Возвращает: список кортежей (agent_id, phone, fullname, current_balance)
    """
    conn = sqlite3.connect("loyalty.db")
    
    query = """
    SELECT 
        um.agent_id,
        um.phone,
        um.fullname,
        COALESCE(b.balance, 0) as current_balance
    FROM user_map um
    LEFT JOIN bonuses b ON um.agent_id = b.agent_id
    ORDER BY um.fullname
    """
    
    contractors = conn.execute(query).fetchall()
    conn.close()
    
    return contractors

def add_bonus_to_contractor(agent_id: str, bonus_amount: int, description: str) -> bool:
    """
    Начисляет бонусы конкретному контрагенту
    """
    try:
        conn = sqlite3.connect("loyalty.db")
        conn.execute("PRAGMA foreign_keys=ON")
        
        # Обновляем баланс бонусов
        conn.execute(
            """
            INSERT INTO bonuses(agent_id, balance) VALUES(?,?)
            ON CONFLICT(agent_id) DO UPDATE SET balance = balance + ?
            """,
            (agent_id, bonus_amount, bonus_amount),
        )
        
        # Добавляем запись в историю транзакций
        conn.execute(
            """
            INSERT INTO bonus_transactions (agent_id, transaction_type, amount, description)
            VALUES (?, ?, ?, ?)
            """,
            (agent_id, "accrual", bonus_amount, description)
        )
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        log.error(f"Ошибка при начислении бонусов для {agent_id}: {e}")
        return False

def bulk_accrual(bonus_amount: int = 20000):  # 200 рублей = 20000 копеек
    """
    Массовое начисление бонусов всем контрагентам
    """
    log.info("Начинаем массовое начисление бонусов...")
    
    # Получаем всех контрагентов
    contractors = get_all_contractors()
    
    if not contractors:
        log.warning("Контрагенты не найдены в базе данных")
        return
    
    log.info(f"Найдено контрагентов: {len(contractors)}")
    
    # Выводим список для подтверждения
    print("\n" + "="*80)
    print("СПИСОК КОНТРАГЕНТОВ ДЛЯ НАЧИСЛЕНИЯ БОНУСОВ:")
    print("="*80)
    print(f"{'№':<3} {'Имя':<30} {'Телефон':<15} {'Текущий баланс':<15}")
    print("-"*80)
    
    for i, (agent_id, phone, fullname, current_balance) in enumerate(contractors, 1):
        balance_rub = current_balance / 100  # Конвертируем копейки в рубли
        print(f"{i:<3} {fullname[:29]:<30} {phone:<15} {balance_rub:.2f} руб")
    
    print("-"*80)
    print(f"Будет начислено каждому: {bonus_amount/100:.2f} рублей")
    print("="*80)
    
    # Запрашиваем подтверждение
    confirmation = input("\nПродолжить начисление? (y/N): ").strip().lower()
    
    if confirmation != 'y':
        log.info("Операция отменена пользователем")
        return
    
    # Начисляем бонусы
    successful_accruals = 0
    failed_accruals = 0
    description = f"Массовое начисление бонусов {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    print(f"\nНачинаем начисление...")
    
    for i, (agent_id, phone, fullname, current_balance) in enumerate(contractors, 1):
        print(f"[{i}/{len(contractors)}] Начисляем бонусы для {fullname}...", end="")
        
        if add_bonus_to_contractor(agent_id, bonus_amount, description):
            successful_accruals += 1
            new_balance = (current_balance + bonus_amount) / 100
            print(f" ✓ (новый баланс: {new_balance:.2f} руб)")
            log.info(f"Успешно начислено {bonus_amount/100:.2f} руб для {fullname} ({agent_id})")
        else:
            failed_accruals += 1
            print(f" ✗ ОШИБКА")
            log.error(f"Ошибка начисления для {fullname} ({agent_id})")
    
    # Итоговый отчет
    print("\n" + "="*60)
    print("ИТОГОВЫЙ ОТЧЕТ:")
    print("="*60)
    print(f"Всего контрагентов: {len(contractors)}")
    print(f"Успешных начислений: {successful_accruals}")
    print(f"Неудачных начислений: {failed_accruals}")
    print(f"Сумма начисления на одного: {bonus_amount/100:.2f} руб")
    print(f"Общая сумма начислений: {successful_accruals * bonus_amount/100:.2f} руб")
    print("="*60)
    
    log.info(f"Массовое начисление завершено. Успешно: {successful_accruals}, Ошибок: {failed_accruals}")

def export_contractors_to_csv():
    """
    Экспорт всех контрагентов в CSV файл
    """
    import csv
    
    contractors = get_all_contractors()
    
    if not contractors:
        log.warning("Контрагенты не найдены для экспорта")
        return
    
    filename = f"contractors_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Заголовки
        writer.writerow(['Agent ID', 'Телефон', 'Имя', 'Баланс (руб)'])
        
        # Данные
        for agent_id, phone, fullname, balance in contractors:
            balance_rub = balance / 100
            writer.writerow([agent_id, phone, fullname, balance_rub])
    
    log.info(f"Экспорт контрагентов завершен: {filename}")
    print(f"Данные экспортированы в файл: {filename}")

def main():
    """
    Главная функция
    """
    print("Скрипт массового начисления бонусов")
    print("1. Начислить по 200 рублей всем контрагентам")
    print("2. Экспортировать список контрагентов в CSV")
    print("3. Показать текущее состояние базы")
    
    choice = input("\nВыберите действие (1-3): ").strip()
    
    if choice == "1":
        bulk_accrual()
    elif choice == "2":
        export_contractors_to_csv()
    elif choice == "3":
        contractors = get_all_contractors()
        print(f"\nВсего контрагентов в базе: {len(contractors)}")
        for agent_id, phone, fullname, balance in contractors:
            balance_rub = balance / 100
            print(f"- {fullname} ({phone}): {balance_rub:.2f} руб")
    else:
        print("Неверный выбор")

if __name__ == "__main__":
    main()
