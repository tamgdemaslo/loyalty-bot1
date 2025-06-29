from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types
from aiogram.types import WebAppInfo
from .formatting import fmt_date_local
from .config import MINIAPP_URL

# Эмодзи грузовика
E_TRUCK = "🚛"

def shipments_kb(docs):
    kb = InlineKeyboardBuilder()
    for d in docs:
        kb.button(
            text=f"{E_TRUCK} №{d.get('name') or d['id'][:8]} • {fmt_date_local(d['moment'])}",
            callback_data=f"ship_{d['id']}"
        )
    kb.adjust(1)
    return kb.as_markup()

def main_menu_premium():
    """Премиальное главное меню с улучшенным дизайном"""
    kb = ReplyKeyboardBuilder()
    
    # Первый ряд - основные финансовые действия
    kb.row(
        types.KeyboardButton(text="💎 Баланс"),
        types.KeyboardButton(text="🎁 Списать баллы")
    )
    
    # Второй ряд - история и аналитика
    kb.row(
        types.KeyboardButton(text="📊 История"),
        types.KeyboardButton(text="📈 Аналитика")
    )
    
    # Третий ряд - сервисы
    kb.row(
        types.KeyboardButton(text="🔧 ТО"),
        types.KeyboardButton(text="📅 Записаться")
    )
    
    # Четвертый ряд - профиль и поддержка
    kb.row(
        types.KeyboardButton(text="👤 Профиль"),
        types.KeyboardButton(text="💬 Поддержка")
    )
    
    return kb.as_markup(resize_keyboard=True)

def balance_detail_kb():
    """Расширенная клавиатура для раздела баланса"""
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="📊 Мой статус", callback_data="show_status"),
        types.InlineKeyboardButton(text="🎁 Привилегии", callback_data="show_benefits")
    )
    kb.row(
        types.InlineKeyboardButton(text="📝 История операций", callback_data="show_transactions"),
        types.InlineKeyboardButton(text="🏆 Достижения", callback_data="show_achievements")
    )
    return kb.as_markup()

def profile_menu_kb():
    """Меню профиля с дополнительными опциями"""
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="✏️ Редактировать", callback_data="profile_edit"),
        types.InlineKeyboardButton(text="🔔 Уведомления", callback_data="profile_notifications")
    )
    kb.row(
        types.InlineKeyboardButton(text="🚗 Мои автомобили", callback_data="profile_cars"),
        types.InlineKeyboardButton(text="📞 Контакты", callback_data="profile_contacts")
    )
    kb.row(
        types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="profile_settings")
    )
    return kb.as_markup()

def support_menu_kb():
    """Меню поддержки"""
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="❓ Частые вопросы", callback_data="support_faq"),
        types.InlineKeyboardButton(text="📞 Связаться", callback_data="support_contact")
    )
    kb.row(
        types.InlineKeyboardButton(text="📋 Руководство", callback_data="support_guide"),
        types.InlineKeyboardButton(text="💡 Предложения", callback_data="support_feedback")
    )
    return kb.as_markup()

def start_choice_kb():
    """Клавиатура выбора интерфейса при старте"""
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(
            text="🌟 Открыть приложение", 
            web_app=types.WebAppInfo(url=MINIAPP_URL)
        )
    )
    kb.row(
        types.InlineKeyboardButton(text="💬 Продолжить в чате", callback_data="continue_chat")
    )
    return kb.as_markup()

def mini_app_menu_kb():
    """Главное меню с веб-приложением"""
    kb = ReplyKeyboardBuilder()
    
    # Первый ряд - веб-приложение и баланс
    kb.row(
        types.KeyboardButton(
            text="🌟 Приложение", 
            web_app=types.WebAppInfo(url=MINIAPP_URL)
        ),
        types.KeyboardButton(text="💎 Баланс")
    )
    
    # Второй ряд - основные действия
    kb.row(
        types.KeyboardButton(text="🎁 Списать баллы"),
        types.KeyboardButton(text="📅 Записаться")
    )
    
    # Третий ряд - дополнительные функции
    kb.row(
        types.KeyboardButton(text="📊 История"),
        types.KeyboardButton(text="🔧 ТО"),
        types.KeyboardButton(text="👤 Профиль")
    )
    
    return kb.as_markup(resize_keyboard=True)
