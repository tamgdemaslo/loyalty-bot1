"""
🎨 UX-оптимизированные клавиатуры с персонализацией
Создано на основе исследования пользовательского опыта
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types
from .formatting import fmt_date_local, fmt_money
from .loyalty import get_level_info, calculate_level_by_spent, get_redeem_cap
from .db import get_balance, get_agent_id
from .config import MINIAPP_URL
from datetime import datetime
import random

def get_user_profile(user_id: int) -> dict:
    """Получает профиль пользователя для персонализации"""
    agent_id = get_agent_id(user_id)
    if not agent_id:
        return {"level": "new", "balance": 0, "visits": 0, "loyalty_level": "Новичок", "loyalty_progress": 0}
    
    balance = get_balance(agent_id)
    
    # Для простоты используем статические данные, в реальности нужно получать из базы
    total_spent = 25000  # Примерная сумма трат
    level_id = calculate_level_by_spent(total_spent)
    level_info = get_level_info(level_id)
    
    # Простая логика определения опытности пользователя
    visits = 5  # TODO: получать из базы
    
    if level_info["name"] in ["Новичок"] and visits < 3:
        profile_type = "new"
    elif level_info["name"] in ["Серебро", "Золото"]:
        profile_type = "experienced"
    else:
        profile_type = "vip"
    
    # Расчет прогресса к следующему уровню
    next_level_id = level_id + 1
    progress = 0.0
    if next_level_id <= 4:  # Максимальный уровень
        from .loyalty import LOYALTY_LEVELS
        next_level = LOYALTY_LEVELS.get(next_level_id)
        if next_level:
            progress_made = total_spent - level_info["min_spent"]
            needed = next_level["min_spent"] - level_info["min_spent"]
            progress = min(1.0, progress_made / needed) if needed > 0 else 1.0
    
    return {
        "level": profile_type,
        "balance": balance,
        "visits": visits,
        "loyalty_level": level_info["name"],
        "loyalty_progress": progress
    }

def smart_welcome_message(user_name: str, user_id: int) -> tuple[str, types.InlineKeyboardMarkup]:
    """
    🚀 Персонализированное приветствие на основе профиля пользователя
    """
    profile = get_user_profile(user_id)
    
    # Определяем время суток для контекстного приветствия
    hour = datetime.now().hour
    if 6 <= hour < 12:
        time_greeting = "Доброе утро"
    elif 12 <= hour < 18:
        time_greeting = "Добрый день"
    else:
        time_greeting = "Добрый вечер"
    
    if profile["level"] == "new":
        # Для новых пользователей - простое и дружелюбное приветствие
        message = (
            f"👋 {time_greeting}, {user_name}!\n\n"
            f"🌟 Добро пожаловать в систему лояльности!\n\n"
            f"💰 Ваши приветственные бонусы: {fmt_money(profile['balance'])}\n\n"
            f"🎯 Выберите, как продолжить:"
        )
        
        kb = InlineKeyboardBuilder()
        kb.row(
            types.InlineKeyboardButton(
                text="🌟 Открыть приложение", 
                web_app=types.WebAppInfo(url=MINIAPP_URL)
            )
        )
        kb.row(
            types.InlineKeyboardButton(text="💡 Как это работает?", callback_data="onboarding_start"),
            types.InlineKeyboardButton(text="💬 Продолжить в чате", callback_data="continue_chat")
        )
        
    elif profile["level"] == "experienced":
        # Для опытных пользователей - показываем прогресс и рекомендации
        message = (
            f"👋 {time_greeting}, {user_name}!\n\n"
            f"🎯 Ваш статус: {profile['loyalty_level']} ⭐\n"
            f"💰 Баланс: {fmt_money(profile['balance'])}\n\n"
            f"📊 Прогресс до следующего уровня:\n"
            f"{'▓' * int(profile['loyalty_progress'] * 10)}{'░' * (10 - int(profile['loyalty_progress'] * 10))} {profile['loyalty_progress']:.0%}\n\n"
            f"🔥 Рекомендации на сегодня:\n"
            f"• Пора записаться на ТО\n"
            f"• Доступна скидка 15% на запчасти"
        )
        
        kb = InlineKeyboardBuilder()
        kb.row(
            types.InlineKeyboardButton(
                text="🌟 Открыть приложение", 
                web_app=types.WebAppInfo(url=MINIAPP_URL)
            )
        )
        kb.row(
            types.InlineKeyboardButton(text="📅 Записаться на ТО", callback_data="quick_booking"),
            types.InlineKeyboardButton(text="💬 Продолжить в чате", callback_data="continue_chat")
        )
        
    else:  # VIP пользователи
        # Для VIP - эксклюзивный контент и быстрые действия
        message = (
            f"👋 {time_greeting}, {user_name}!\n\n"
            f"👑 Ваш VIP статус: {profile['loyalty_level']}\n"
            f"💎 Баланс: {fmt_money(profile['balance'])}\n\n"
            f"🌟 Эксклюзивные предложения:\n"
            f"• Приоритетная запись\n"
            f"• Персональный менеджер\n"
            f"• Списание до 40% от чека\n\n"
            f"⚡ Быстрые действия:"
        )
        
        kb = InlineKeyboardBuilder()
        kb.row(
            types.InlineKeyboardButton(
                text="🌟 VIP-приложение", 
                web_app=types.WebAppInfo(url=MINIAPP_URL)
            )
        )
        kb.row(
            types.InlineKeyboardButton(text="🎁 Списать бонусы", callback_data="quick_redeem"),
            types.InlineKeyboardButton(text="📅 Приоритетная запись", callback_data="vip_booking")
        )
        kb.row(
            types.InlineKeyboardButton(text="💬 Продолжить в чате", callback_data="continue_chat")
        )
    
    return message, kb.as_markup()

def adaptive_main_menu(user_id: int) -> types.ReplyKeyboardMarkup:
    """
    Минималистичное главное меню без избытка эмодзи
    """
    kb = ReplyKeyboardBuilder()
    
    # Упрощенное универсальное меню для всех пользователей
    kb.row(
        types.KeyboardButton(text="Баланс"),
        types.KeyboardButton(text="Записаться в сервис")
    )
    kb.row(
        types.KeyboardButton(text="История посещений"),
        types.KeyboardButton(text="Профиль")
    )
    kb.row(
        types.KeyboardButton(text="Связаться")
    )
    
    return kb.as_markup(resize_keyboard=True)

def smart_balance_kb(user_id: int) -> types.InlineKeyboardMarkup:
    """
    💰 Умная клавиатура для раздела баланса с персонализированными действиями
    """
    profile = get_user_profile(user_id)
    kb = InlineKeyboardBuilder()
    
    # Основная информация всегда доступна
    kb.row(
        types.InlineKeyboardButton(text="📊 Мой статус", callback_data="show_status"),
        types.InlineKeyboardButton(text="🎁 Привилегии", callback_data="show_benefits")
    )
    
    if profile["balance"] > 0:
        # Если есть бонусы - показываем умные рекомендации по использованию
        kb.row(
            types.InlineKeyboardButton(text="💡 Как лучше потратить?", callback_data="spending_recommendations"),
            types.InlineKeyboardButton(text="📝 История операций", callback_data="show_transactions")
        )
    else:
        # Если нет бонусов - показываем как их заработать
        kb.row(
            types.InlineKeyboardButton(text="💡 Как заработать бонусы?", callback_data="earning_tips"),
            types.InlineKeyboardButton(text="📝 История операций", callback_data="show_transactions")
        )
    
    if profile["level"] in ["experienced", "vip"]:
        # Для опытных пользователей добавляем достижения
        kb.row(
            types.InlineKeyboardButton(text="🏆 Достижения", callback_data="show_achievements")
        )
    
    return kb.as_markup()

def contextual_notification_kb(notification_type: str) -> types.InlineKeyboardMarkup:
    """
    📱 Контекстные уведомления с релевантными действиями
    """
    kb = InlineKeyboardBuilder()
    
    if notification_type == "maintenance_due":
        kb.row(
            types.InlineKeyboardButton(text="📅 Записаться сейчас", callback_data="quick_booking"),
            types.InlineKeyboardButton(text="⏰ Напомнить через неделю", callback_data="remind_later")
        )
    elif notification_type == "discount_expiring":
        kb.row(
            types.InlineKeyboardButton(text="📅 Воспользоваться", callback_data="use_discount"),
            types.InlineKeyboardButton(text="⏰ Напомнить завтра", callback_data="remind_tomorrow")
        )
    elif notification_type == "new_achievement":
        kb.row(
            types.InlineKeyboardButton(text="🎁 Забрать награду", callback_data="claim_reward"),
            types.InlineKeyboardButton(text="👀 Все достижения", callback_data="show_achievements")
        )
    elif notification_type == "status_upgrade":
        kb.row(
            types.InlineKeyboardButton(text="🎁 Использовать бонусы", callback_data="use_bonus"),
            types.InlineKeyboardButton(text="📊 Мои привилегии", callback_data="show_benefits")
        )
    
    return kb.as_markup()

def gamification_progress_kb(current_level: str, progress: float) -> types.InlineKeyboardMarkup:
    """
    🎮 Клавиатура с геймификацией и мотивационными элементами
    """
    kb = InlineKeyboardBuilder()
    
    # Всегда показываем прогресс к следующему уровню
    kb.row(
        types.InlineKeyboardButton(text="🎯 План действий", callback_data="action_plan"),
        types.InlineKeyboardButton(text="📊 Детальный прогресс", callback_data="detailed_progress")
    )
    
    # Если прогресс больше 80% - мотивируем на финальный рывок
    if progress > 0.8:
        kb.row(
            types.InlineKeyboardButton(text="🚀 Финальный рывок!", callback_data="final_push")
        )
    
    # Добавляем социальный элемент
    kb.row(
        types.InlineKeyboardButton(text="👥 Пригласить друга (+2x бонус)", callback_data="invite_friend"),
        types.InlineKeyboardButton(text="🏆 Рейтинг клиентов", callback_data="leaderboard")
    )
    
    return kb.as_markup()

def smart_booking_flow_kb(step: str, context: dict = None) -> types.InlineKeyboardMarkup:
    """
    📅 Умная клавиатура для записи с рекомендациями
    """
    kb = InlineKeyboardBuilder()
    
    if step == "service_selection":
        # Первый экран - показываем рекомендуемые услуги на основе ТО
        if context and context.get("recommended_services"):
            kb.row(
                types.InlineKeyboardButton(text="🎯 Выбрать рекомендуемое", callback_data="select_recommended")
            )
        
        kb.row(
            types.InlineKeyboardButton(text="📋 Все услуги", callback_data="all_services"),
            types.InlineKeyboardButton(text="🔍 Поиск услуги", callback_data="search_service")
        )
        
    elif step == "master_selection":
        # Выбор мастера - показываем предпочтительного мастера
        if context and context.get("preferred_master"):
            kb.row(
                types.InlineKeyboardButton(text="🌟 Ваш мастер", callback_data="preferred_master")
            )
        
        kb.row(
            types.InlineKeyboardButton(text="👥 Все мастера", callback_data="all_masters"),
            types.InlineKeyboardButton(text="⚡ Первый доступный", callback_data="any_master")
        )
        
    elif step == "time_selection":
        # Выбор времени - показываем удобные слоты
        kb.row(
            types.InlineKeyboardButton(text="⚡ Ближайший слот", callback_data="next_slot"),
            types.InlineKeyboardButton(text="📅 Выбрать дату", callback_data="select_date")
        )
        
        if context and context.get("preferred_times"):
            kb.row(
                types.InlineKeyboardButton(text="⭐ Ваши удобные часы", callback_data="preferred_times")
            )
    
    # Всегда добавляем кнопку отмены
    kb.row(
        types.InlineKeyboardButton(text="◀️ Назад", callback_data="booking_back"),
        types.InlineKeyboardButton(text="❌ Отмена", callback_data="booking_cancel")
    )
    
    return kb.as_markup()

def onboarding_kb(step: int) -> types.InlineKeyboardMarkup:
    """
    🚀 Клавиатура для процесса онбординга новых пользователей
    """
    kb = InlineKeyboardBuilder()
    
    if step == 1:
        # Первый шаг - начало онбординга
        kb.row(
            types.InlineKeyboardButton(text="🚀 Начать настройку", callback_data="onboarding_step_2"),
            types.InlineKeyboardButton(text="⏭ Пропустить", callback_data="onboarding_skip")
        )
    elif step == 2:
        # Второй шаг - информация об автомобиле
        kb.row(
            types.InlineKeyboardButton(text="📝 Добавить авто", callback_data="add_car"),
            types.InlineKeyboardButton(text="⏭ Позже", callback_data="onboarding_step_3")
        )
    elif step == 3:
        # Третий шаг - выбор первого действия
        kb.row(
            types.InlineKeyboardButton(text="📅 Записаться на ТО", callback_data="first_booking"),
            types.InlineKeyboardButton(text="📊 Изучить историю", callback_data="show_history")
        )
        kb.row(
            types.InlineKeyboardButton(text="💡 Узнать о бонусах", callback_data="bonus_info"),
            types.InlineKeyboardButton(text="🏠 В главное меню", callback_data="to_main_menu")
        )
    
    return kb.as_markup()

def personalized_support_kb(user_id: int) -> types.InlineKeyboardMarkup:
    """
    💬 Персонализированная поддержка на основе профиля пользователя
    """
    profile = get_user_profile(user_id)
    kb = InlineKeyboardBuilder()
    
    if profile["level"] == "new":
        # Для новых пользователей - базовая помощь
        kb.row(
            types.InlineKeyboardButton(text="❓ Как работает система?", callback_data="system_help"),
            types.InlineKeyboardButton(text="💡 Первые шаги", callback_data="first_steps")
        )
        kb.row(
            types.InlineKeyboardButton(text="📞 Связаться с нами", callback_data="contact_support")
        )
    else:
        # Для опытных пользователей - расширенная помощь
        kb.row(
            types.InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq"),
            types.InlineKeyboardButton(text="📋 Руководство", callback_data="user_guide")
        )
        kb.row(
            types.InlineKeyboardButton(text="📞 Связаться", callback_data="contact_support"),
            types.InlineKeyboardButton(text="💡 Предложения", callback_data="feedback")
        )
    
    if profile["level"] == "vip":
        # Для VIP - персональная поддержка
        kb.row(
            types.InlineKeyboardButton(text="👑 VIP поддержка", callback_data="vip_support")
        )
    
    return kb.as_markup()

# Функции для генерации мотивационных сообщений
def get_motivational_tip(user_id: int) -> str:
    """Возвращает мотивационный совет на основе профиля пользователя"""
    profile = get_user_profile(user_id)
    
    tips = {
        "new": [
            "💡 Записывайтесь на ТО через бот и получайте двойные бонусы!",
            "🎯 Каждое посещение приближает вас к Silver статусу!",
            "⭐ Пригласите друга и получите +500 бонусов!"
        ],
        "experienced": [
            "🚀 До следующего уровня осталось совсем немного!",
            "💎 Используйте бонусы с умом - экономьте до 30%!",
            "🏆 Ваш рейтинг среди клиентов растет!"
        ],
        "vip": [
            "👑 Как VIP клиент, вы получаете максимальные привилегии!",
            "🌟 Ваш персональный менеджер всегда готов помочь!",
            "💎 Эксклюзивные предложения только для вас!"
        ]
    }
    
    return random.choice(tips.get(profile["level"], tips["new"]))
