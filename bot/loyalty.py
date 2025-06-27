# loyalty-bot/bot/loyalty.py
"""
Система уровней лояльности для автосервиса
"""

from typing import Dict, Any
from .formatting import fmt_money

# Конфигурация уровней лояльности
LOYALTY_LEVELS = {
    1: {
        "name": "Новичок",
        "emoji": "🌱",
        "min_spent": 0,
        "bonus_rate": 0.05,  # 5%
        "redeem_cap": 0.30,  # 30%
        "description": "Добро пожаловать в нашу программу лояльности!",
        "benefits": [
            "5% бонусов с покупок",
            "Возможность списать до 30% от чека"
        ]
    },
    2: {
        "name": "Серебро",
        "emoji": "🥈",
        "min_spent": 1500000,  # 15000 рублей
        "bonus_rate": 0.07,  # 7%
        "redeem_cap": 0.35,  # 35%
        "description": "Вы становитесь постоянным клиентом!",
        "benefits": [
            "7% бонусов с покупок",
            "Возможность списать до 35% от чека",
            "Уведомления о специальных предложениях"
        ]
    },
    3: {
        "name": "Золото",
        "emoji": "🥇",
        "min_spent": 4000000,  # 40000 рублей
        "bonus_rate": 0.10,  # 10%
        "redeem_cap": 0.40,  # 40%
        "description": "Золотой статус открывает новые возможности!",
        "benefits": [
            "10% бонусов с покупок",
            "Возможность списать до 40% от чека",
            "Приоритетная запись на сервис",
            "Персональные скидки"
        ]
    },
    4: {
        "name": "Платина",
        "emoji": "💎",
        "min_spent": 10000000,  # 100000 рублей
        "bonus_rate": 0.15,  # 15%
        "redeem_cap": 0.50,  # 50%
        "description": "Максимальный уровень VIP-обслуживания!",
        "benefits": [
            "15% бонусов с покупок",
            "Возможность списать до 50% от чека",
            "VIP-обслуживание",
            "Бесплатная диагностика",
            "Максимальные скидки на услуги"
        ]
    }
}


def calculate_level_by_spent(total_spent: int) -> int:
    """Определяет уровень клиента по общей сумме трат"""
    for level_id in sorted(LOYALTY_LEVELS.keys(), reverse=True):
        if total_spent >= LOYALTY_LEVELS[level_id]["min_spent"]:
            return level_id
    return 1


def get_level_info(level_id: int) -> Dict[str, Any]:
    """Возвращает информацию об уровне лояльности"""
    return LOYALTY_LEVELS.get(level_id, LOYALTY_LEVELS[1])


def get_bonus_rate(level_id: int) -> float:
    """Возвращает процент начисления бонусов для уровня"""
    return get_level_info(level_id)["bonus_rate"]


def get_redeem_cap(level_id: int) -> float:
    """Возвращает максимальный процент списания для уровня"""
    return get_level_info(level_id)["redeem_cap"]


def format_level_status(level_id: int, total_spent: int) -> str:
    """Форматирует статус клиента для отображения"""
    level_info = get_level_info(level_id)
    
    # Определяем прогресс до следующего уровня
    next_level_id = level_id + 1
    if next_level_id in LOYALTY_LEVELS:
        next_level = LOYALTY_LEVELS[next_level_id]
        progress = total_spent - level_info["min_spent"]
        needed = next_level["min_spent"] - level_info["min_spent"]
        progress_percent = min(100, (progress / needed) * 100) if needed > 0 else 100
        
        status_text = (
            f"{level_info['emoji']} <b>{level_info['name']}</b>\n"
            f"💰 Потрачено: <b>{fmt_money(total_spent)}</b>\n"
            f"📊 Прогресс до {next_level['emoji']} {next_level['name']}: "
            f"<b>{progress_percent:.1f}%</b>\n"
            f"🎯 До повышения: <b>{fmt_money(next_level['min_spent'] - total_spent)}</b>"
        )
    else:
        status_text = (
            f"{level_info['emoji']} <b>{level_info['name']}</b>\n"
            f"💰 Потрачено: <b>{fmt_money(total_spent)}</b>\n"
            f"🏆 <b>Максимальный уровень достигнут!</b>"
        )
    
    return status_text


def format_level_benefits(level_id: int) -> str:
    """Форматирует список привилегий уровня"""
    level_info = get_level_info(level_id)
    
    benefits_text = f"<b>{level_info['emoji']} Привилегии уровня {level_info['name']}:</b>\n\n"
    
    for i, benefit in enumerate(level_info["benefits"], 1):
        benefits_text += f"• {benefit}\n"
    
    return benefits_text


def get_level_up_message(old_level: int, new_level: int) -> str:
    """Создает сообщение о повышении уровня"""
    new_level_info = get_level_info(new_level)
    
    message = (
        f"🎉 <b>Поздравляем с повышением!</b>\n\n"
        f"Ваш новый статус: {new_level_info['emoji']} <b>{new_level_info['name']}</b>\n\n"
        f"{new_level_info['description']}\n\n"
        f"{format_level_benefits(new_level)}"
    )
    
    return message
