"""
📝 Минималистичные UX тексты для бота
Сдержанные, профессиональные, без избытка эмодзи
"""

from datetime import datetime
from typing import List, Dict

class WelcomeTexts:
    """Тексты приветствия - сдержанные и дружелюбные"""
    
    @staticmethod
    def new_user_greeting():
        return (
            "Добро пожаловать в личный кабинет!\n\n"
            "Здесь вы сможете:\n"
            "• Отслеживать баланс бонусов\n"
            "• Записываться на обслуживание\n"
            "• Смотреть историю визитов\n\n"
            "Для начала работы поделитесь номером телефона"
        )
    
    @staticmethod
    def returning_user(name: str, status: str, balance: int, time_greeting: str = ""):
        greeting = f"{time_greeting}, {name}!" if time_greeting else f"Привет, {name}!"
        
        return (
            f"{greeting}\n\n"
            f"Ваш статус: {status}\n"
            f"Баланс: {balance:,} ₽\n\n"
            "Что будем делать?"
        )
    
    @staticmethod
    def new_client_name_request():
        return "Как к вам обращаться?"
    
    @staticmethod
    def profile_created():
        return (
            "Отлично! Профиль создан.\n\n"
            "Теперь вы можете получать бонусы за покупки "
            "и тратить их на обслуживание."
        )

class BalanceTexts:
    """Тексты для работы с балансом"""
    
    @staticmethod
    def empty_balance(status: str):
        return (
            "Баланс: 0 ₽\n\n"
            "Бонусы начисляются автоматически после каждого посещения.\n"
            "Приходите на обслуживание — и бонусы не заставят себя ждать!"
        )
    
    @staticmethod
    def small_balance(balance: int, status: str):
        return (
            f"Баланс: {balance:,} ₽\n\n"
            f"Накопленных бонусов хватит на мелкие услуги или доплату к ТО.\n"
            f"Продолжайте пользоваться нашими услугами для накопления большей суммы."
        )
    
    @staticmethod
    def good_balance(balance: int, status: str, max_redeem: int):
        return (
            f"Баланс: {balance:,} ₽\n\n"
            f"Отличная сумма! Можете потратить до {max_redeem:,} ₽ на следующее ТО.\n"
            f"Ваш статус «{status}» даёт дополнительные скидки."
        )

class BookingTexts:
    """Тексты для записи на услуги"""
    
    @staticmethod
    def booking_start():
        return "Записываем на обслуживание..."
    
    @staticmethod
    def service_recommendations(services: List[str]):
        if not services:
            return "Выберите нужную услугу из каталога"
        
        message = "Рекомендуем для вашего авто:\n\n"
        for service in services:
            message += f"• {service}\n"
        
        message += "\nИли выберите любую услугу из каталога"
        return message
    
    @staticmethod
    def master_selection(master_name: str):
        return f"Мастер: {master_name}"
    
    @staticmethod
    def time_selection():
        return "Выберите удобное время"

class RedeemTexts:
    """Тексты для списания бонусов"""
    
    @staticmethod
    def no_balance():
        return (
            "Бонусов пока нет.\n\n"
            "Они появятся после первого посещения сервиса."
        )
    
    @staticmethod
    def redeem_scenarios(balance: int, scenarios: List[Dict]):
        message = f"Доступно: {balance:,} ₽\n\nВарианты использования:\n\n"
        
        for scenario in scenarios:
            message += (
                f"{scenario['service']}\n"
                f"Экономия: {scenario['savings']:,} ₽\n"
                f"Остаток: {scenario['remaining']:,} ₽\n\n"
            )
        
        return message

class AnalyticsTexts:
    """Тексты аналитики"""
    
    @staticmethod
    def user_stats(status: str, balance: int, visits: int, progress: float):
        return (
            f"Статус: {status}\n"
            f"Баланс: {balance:,} ₽\n"
            f"Посещений: {visits}\n"
            f"Прогресс к следующему уровню: {progress:.0%}"
        )
    
    @staticmethod
    def visit_history_empty():
        return "История посещений пока пуста"

class MaintenanceTexts:
    """Тексты техобслуживания"""
    
    @staticmethod
    def maintenance_overview():
        return "Статус технического обслуживания"
    
    @staticmethod
    def maintenance_reminder(service: str, km_left: int):
        if km_left > 0:
            return f"Напоминание: {service} через {km_left} км"
        return f"Время для: {service}"

class SupportTexts:
    """Тексты поддержки"""
    
    @staticmethod
    def support_menu(level: str):
        return (
            "Служба поддержки\n\n"
            "Мы поможем с любыми вопросами по программе лояльности, "
            "записи на обслуживание или техническими проблемами."
        )
    
    @staticmethod
    def how_it_works():
        return (
            "Как работает программа лояльности:\n\n"
            "• За каждую покупку начисляются бонусы\n"
            "• Бонусы можно тратить на услуги\n"
            "• Чем больше тратите, тем выше статус\n"
            "• Высокий статус = больше привилегий"
        )
    
    @staticmethod
    def contact_info():
        return (
            "Контакты службы поддержки:\n\n"
            "Телефон: +7 (XXX) XXX-XX-XX\n"
            "Email: support@example.com\n\n"
            "Работаем ежедневно с 9:00 до 21:00"
        )

class ErrorTexts:
    """Тексты ошибок"""
    
    @staticmethod
    def auth_required():
        return (
            "Нужна авторизация.\n\n"
            "Поделитесь номером телефона для продолжения работы."
        )
    
    @staticmethod
    def general_error():
        return (
            "Произошла техническая ошибка.\n\n"
            "Попробуйте повторить действие через минуту."
        )

class GamificationTexts:
    """Упрощённые тексты геймификации"""
    
    @staticmethod
    def new_achievement(title: str, reward: int):
        return (
            f"Достижение разблокировано: {title}\n"
            f"Бонус: +{reward} ₽"
        )
    
    @staticmethod
    def level_up(old_level: str, new_level: str, benefits: List[str]):
        message = f"Статус повышен: {old_level} → {new_level}\n\n"
        if benefits:
            message += "Новые возможности:\n"
            for benefit in benefits:
                message += f"• {benefit}\n"
        return message

class TextHelpers:
    """Вспомогательные функции для текстов"""
    
    @staticmethod
    def get_time_greeting():
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return "Доброе утро"
        elif 12 <= hour < 18:
            return "Добрый день"
        elif 18 <= hour < 23:
            return "Добрый вечер"
        else:
            return "Доброй ночи"
    
    @staticmethod
    def format_list(items: List[str]) -> str:
        return "\n".join(f"• {item}" for item in items)
    
    @staticmethod
    def format_money(amount: int) -> str:
        return f"{amount:,} ₽"

class DynamicTexts:
    """Динамические тексты"""
    
    @staticmethod
    def countdown_text(days: int, action: str) -> str:
        if days == 0:
            return f"{action} сегодня"
        elif days == 1:
            return f"{action} завтра"
        else:
            return f"{action} через {days} дн."
    
    @staticmethod
    def progress_text(current: int, target: int, unit: str = "") -> str:
        progress = (current / target) * 100 if target > 0 else 0
        return f"{current}/{target} {unit} ({progress:.0f}%)"

# Экспорт всех классов
__all__ = [
    'WelcomeTexts', 'BalanceTexts', 'BookingTexts', 'RedeemTexts',
    'AnalyticsTexts', 'MaintenanceTexts', 'SupportTexts', 'ErrorTexts',
    'GamificationTexts', 'TextHelpers', 'DynamicTexts'
]
