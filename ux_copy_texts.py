"""
📝 UX-копирайтинг для Telegram бота
Улучшенные тексты интерфейса, основанные на принципах эффективной коммуникации
"""

from typing import Dict, List

# Локальная функция для форматирования денег
def fmt_money(amount: int) -> str:
    """Форматирование суммы в удобочитаемый вид"""
    if amount == 0:
        return "0 ₽"
    return f"{amount:,} ₽".replace(",", " ")

# ═══════════════════════════════════════════════════════════════════
# 🎯 ПРИНЦИПЫ UX-КОПИРАЙТИНГА
# ═══════════════════════════════════════════════════════════════════

"""
1. ЯСНОСТЬ - каждое слово должно быть понятным
2. КРАТКОСТЬ - убираем лишние слова, оставляем суть
3. ЧЕЛОВЕЧНОСТЬ - говорим как живые люди, не как роботы
4. ДЕЙСТВИЕ - каждый текст должен вести к конкретному действию
5. ПОЛЬЗА - объясняем ЧТО получит пользователь
6. КОНТЕКСТ - учитываем ситуацию и настроение пользователя
"""

# ═══════════════════════════════════════════════════════════════════
# 🚀 ТЕКСТЫ ДЛЯ ПРИВЕТСТВИЯ И ОНБОРДИНГА
# ═══════════════════════════════════════════════════════════════════

class WelcomeTexts:
    @staticmethod
    def new_user_greeting() -> str:
        """Приветствие для нового пользователя"""
        return (
            "🎉 Рады видеть вас!\n\n"
            "Это ваша программа лояльности в автосервисе:\n\n"
            "💰 Получайте бонусы за каждое посещение\n"
            "📱 Записывайтесь онлайн — это быстро\n"
            "🔧 Следите за ТО автомобиля\n"
            "🎁 Экономьте до 40% на услугах\n\n"
            "👆 Чтобы начать, поделитесь номером телефона"
        )
    
    @staticmethod
    def returning_user(name: str, status: str, balance: int, time_greeting: str) -> str:
        """Приветствие для вернувшегося пользователя"""
        return (
            f"{time_greeting}, {name}! 👋\n\n"
            f"🎯 Ваш статус: {status}\n"
            f"💰 На счёте: {fmt_money(balance)}\n\n"
            "🚀 Что будем делать?"
        )
    
    @staticmethod
    def new_client_name_request() -> str:
        """Запрос имени у нового клиента"""
        return (
            "🙋‍♂️ Как к вам обращаться?\n\n"
            "Введите ваше имя (или как вам удобно).\n"
            "Так мы сделаем общение личным и дружелюбным."
        )
    
    @staticmethod
    def profile_created() -> str:
        """Подтверждение создания профиля"""
        return (
            "🎉 Отлично! Профиль создан\n\n"
            "🎁 Ваш подарок: 100 бонусных рублей\n"
            "🥉 Стартовый статус: Новичок\n\n"
            "✨ С каждым посещением вы будете получать больше бонусов!"
        )
    
    @staticmethod
    def onboarding_offer() -> str:
        """Предложение настройки профиля"""
        return (
            "🚗 Расскажете о своём автомобиле?\n\n"
            "Это поможет:\n"
            "• Напоминать о плановом ТО\n"
            "• Предлагать нужные услуги\n"
            "• Делать персональные скидки\n\n"
            "⏱ Займёт всего 30 секунд"
        )
    
    @staticmethod
    def onboarding_complete() -> str:
        """Завершение настройки"""
        return (
            "🏁 Готово! Всё настроено\n\n"
            "💰 Бонус за настройку: 100 ₽\n\n"
            "🎯 С чего начнём?"
        )
    
    @staticmethod
    def onboarding_skip() -> str:
        """Пропуск настройки"""
        return (
            "👌 Без проблем!\n\n"
            "Настроить профиль можно в любой момент через меню 👤 Профиль"
        )

# ═══════════════════════════════════════════════════════════════════
# 💰 ТЕКСТЫ ДЛЯ РАБОТЫ С БАЛАНСОМ
# ═══════════════════════════════════════════════════════════════════

class BalanceTexts:
    @staticmethod
    def empty_balance(status: str) -> str:
        """Пустой баланс"""
        return (
            f"💳 Ваш бонусный счёт\n\n"
            f"💰 Баланс: 0 ₽\n"
            f"🎯 Статус: {status}\n\n"
            f"💡 Как заработать первые бонусы:\n"
            f"• 📅 Запишитесь на ТО — получите кэшбек\n"
            f"• 👥 Пригласите друга — получите 500 ₽\n"
            f"• 🔄 Чаще посещайте сервис — выше статус"
        )
    
    @staticmethod
    def small_balance(balance: int, status: str) -> str:
        """Небольшой баланс"""
        return (
            f"💳 Ваш бонусный счёт\n\n"
            f"💰 Баланс: {fmt_money(balance)}\n"
            f"🎯 Статус: {status}\n\n"
            f"🎯 Совсем скоро сможете:\n"
            f"• 🧼 Оплатить мойку бонусами\n"
            f"• 💰 Получить скидку на ТО\n\n"
            f"💪 Продолжайте копить!"
        )
    
    @staticmethod
    def good_balance(balance: int, status: str, max_redeem: int) -> str:
        """Хороший баланс"""
        return (
            f"💳 Ваш бонусный счёт\n\n"
            f"💰 Баланс: {fmt_money(balance)}\n"
            f"🎯 Статус: {status}\n\n"
            f"🎁 Можете потратить прямо сейчас:\n"
            f"• На ТО: до {fmt_money(max_redeem)}\n"
            f"• На запчасти: до {fmt_money(max_redeem)}\n"
            f"• На мойку: {fmt_money(min(balance, 500))}"
        )
    
    @staticmethod
    def spending_recommendations(balance: int) -> str:
        """Рекомендации по тратам"""
        recommendations = []
        
        if balance >= 1000:
            recommendations.append("🔧 Плановое ТО — экономия до 30%")
        if balance >= 500:
            recommendations.append("🛒 Покупка запчастей — экономия до 25%")
        if balance >= 200:
            recommendations.append("🧼 Мойка автомобиля — полная оплата")
        if balance >= 100:
            recommendations.append("🔍 Компьютерная диагностика")
            
        text = f"💡 Лучшие способы потратить {fmt_money(balance)}:\n\n"
        text += "\n".join(f"• {rec}" for rec in recommendations)
        text += "\n\n💬 Записаться на что-то из списка?"
        
        return text
    
    @staticmethod
    def earning_tips(user_level: str) -> str:
        """Советы по заработку бонусов"""
        if user_level == "new":
            tips = [
                "📅 Записывайтесь через бот — двойные бонусы",
                "🔄 Приезжайте регулярно — больше кэшбек",
                "👥 Приводите друзей — по 500₽ за каждого"
            ]
        else:
            tips = [
                "🎯 Повышайте статус — больше привилегий",
                "📈 Увеличивайте сумму заказа — выше процент",
                "⭐ Оставляйте отзывы — дополнительные бонусы"
            ]
        
        return (
            "💡 Как заработать больше бонусов:\n\n" +
            "\n".join(f"• {tip}" for tip in tips) +
            "\n\n🚀 Начинайте прямо сейчас!"
        )

# ═══════════════════════════════════════════════════════════════════
# 📅 ТЕКСТЫ ДЛЯ ЗАПИСИ НА ОБСЛУЖИВАНИЕ
# ═══════════════════════════════════════════════════════════════════

class BookingTexts:
    @staticmethod
    def booking_start() -> str:
        """Начало записи"""
        return "🔍 Подбираем лучшие варианты для вас..."
    
    @staticmethod
    def service_recommendations(recommended: List[str]) -> str:
        """Рекомендуемые услуги"""
        text = "🎯 Рекомендуем для вашего авто:\n\n"
        
        for service in recommended[:2]:
            text += f"✅ {service} (самое время!)\n"
        
        for service in recommended[2:]:
            text += f"⚠️ {service} (скоро понадобится)\n"
        
        text += "\n📋 Или выберите любую услугу из каталога"
        return text
    
    @staticmethod
    def master_selection(preferred_master: str = None) -> str:
        """Выбор мастера"""
        base_text = "👨‍🔧 Кто будет обслуживать ваш автомобиль?\n\n"
        
        if preferred_master:
            text = base_text + f"🌟 {preferred_master} — ваш мастер (уже работал с вами)\n\n"
            text += "Или выберите другого специалиста"
        else:
            text = base_text + "Выберите мастера или возьмём первого свободного"
        
        return text
    
    @staticmethod
    def time_selection() -> str:
        """Выбор времени"""
        return (
            "📅 Когда вам удобно приехать?\n\n"
            "⚡ Покажем ближайшие свободные слоты\n"
            "или выберите удобную дату"
        )
    
    @staticmethod
    def booking_confirmation(date: str, time: str, master: str, service: str, cost: int, bonus_discount: int) -> str:
        """Подтверждение записи"""
        return (
            f"✅ Запись подтверждена!\n\n"
            f"📅 {date} в {time}\n"
            f"👨‍🔧 Мастер: {master}\n"
            f"🔧 Услуга: {service}\n"
            f"💰 Стоимость: ~{fmt_money(cost)}\n\n"
            f"🎁 Можете сэкономить: {fmt_money(bonus_discount)} бонусами"
        )
    
    @staticmethod
    def booking_error() -> str:
        """Ошибка при записи"""
        return (
            "😔 Что-то пошло не так\n\n"
            "Не получилось создать запись.\n"
            "Попробуйте ещё раз или обратитесь к администратору."
        )

# ═══════════════════════════════════════════════════════════════════
# 🎁 ТЕКСТЫ ДЛЯ СПИСАНИЯ БОНУСОВ
# ═══════════════════════════════════════════════════════════════════

class RedeemTexts:
    @staticmethod
    def no_balance() -> str:
        """Нет бонусов для списания"""
        return (
            "💳 На бонусном счёте пусто\n\n"
            "💡 Заработайте бонусы:\n"
            "• Запишитесь на ТО\n"
            "• Пригласите друга\n"
            "• Регулярно посещайте сервис\n\n"
            "🚀 Начните прямо сейчас!"
        )
    
    @staticmethod
    def redeem_scenarios(balance: int, scenarios: List[Dict]) -> str:
        """Сценарии использования бонусов"""
        text = f"💰 Ваши бонусы: {fmt_money(balance)}\n\n🎯 Как лучше потратить:\n\n"
        
        for scenario in scenarios:
            text += (
                f"┌─────────────────────────────────┐\n"
                f"│ {scenario['icon']} {scenario['service']:<20} │\n"
                f"│ Сэкономите: {fmt_money(scenario['savings']):<10} ({scenario['percent']}%) │\n"
                f"│ Останется: {fmt_money(scenario['remaining']):<11} │\n"
                f"└─────────────────────────────────┘\n\n"
            )
        
        return text
    
    @staticmethod
    def redeem_confirmation(amount: int, remaining: int) -> str:
        """Подтверждение списания"""
        return (
            f"✅ Бонусы готовы к списанию\n\n"
            f"💰 Списываем: {fmt_money(amount)}\n"
            f"💳 Останется: {fmt_money(remaining)}\n\n"
            f"Покажите этот экран на кассе"
        )

# ═══════════════════════════════════════════════════════════════════
# 📊 ТЕКСТЫ ДЛЯ СТАТИСТИКИ И АНАЛИТИКИ
# ═══════════════════════════════════════════════════════════════════

class AnalyticsTexts:
    @staticmethod
    def user_stats(status: str, balance: int, visits: int, progress: float) -> str:
        """Статистика пользователя"""
        progress_bar = "▓" * int(progress * 10) + "░" * (10 - int(progress * 10))
        
        return (
            f"📊 Ваша статистика\n\n"
            f"🎯 Статус: {status}\n"
            f"💰 Бонусы: {fmt_money(balance)}\n"
            f"🏃‍♂️ Посещений: {visits}\n\n"
            f"📈 До следующего уровня:\n"
            f"{progress_bar} {progress:.0%}\n\n"
            f"{AnalyticsTexts._get_motivation_message(progress)}"
        )
    
    @staticmethod
    def _get_motivation_message(progress: float) -> str:
        """Мотивационное сообщение в зависимости от прогресса"""
        if progress > 0.8:
            return "🔥 Финальный рывок! Совсем чуть-чуть до повышения!"
        elif progress > 0.5:
            return "🚀 Отличный прогресс! Продолжайте в том же духе!"
        else:
            return "💪 Хорошее начало! Впереди много интересного!"
    
    @staticmethod
    def achievements(achievements: List[str]) -> str:
        """Список достижений"""
        if not achievements:
            return (
                "🏆 Достижения\n\n"
                "Пока здесь пусто, но скоро появятся ваши первые награды!\n\n"
                "💪 Посещайте сервис и открывайте новые достижения"
            )
        
        text = "🏆 Ваши достижения:\n\n"
        text += "\n".join(f"• {achievement}" for achievement in achievements)
        return text
    
    @staticmethod
    def visit_history_empty() -> str:
        """Пустая история посещений"""
        return (
            "📊 История посещений\n\n"
            "🤷‍♂️ Пока нет записей о посещениях\n\n"
            "После первого визита здесь появится история ваших покупок и услуг"
        )

# ═══════════════════════════════════════════════════════════════════
# 🔧 ТЕКСТЫ ДЛЯ ТЕХНИЧЕСКОГО ОБСЛУЖИВАНИЯ
# ═══════════════════════════════════════════════════════════════════

class MaintenanceTexts:
    @staticmethod
    def maintenance_overview() -> str:
        """Обзор ТО"""
        return "🔧 Статус ТО вашего автомобиля\n\nВыберите пункт для подробной информации:"
    
    @staticmethod
    def maintenance_reminder(service: str, km_left: int) -> str:
        """Напоминание о ТО"""
        return (
            f"🚨 Время для ТО!\n\n"
            f"🔧 {service}\n"
            f"📏 Осталось: {km_left} км\n\n"
            f"Запишитесь сейчас, чтобы не забыть"
        )
    
    @staticmethod
    def maintenance_schedule() -> str:
        """Расписание ТО"""
        return (
            "📋 График планового ТО\n\n"
            "Нажмите на любой пункт, чтобы узнать подробности или записаться"
        )

# ═══════════════════════════════════════════════════════════════════
# 💬 ТЕКСТЫ ДЛЯ ПОДДЕРЖКИ
# ═══════════════════════════════════════════════════════════════════

class SupportTexts:
    @staticmethod
    def support_menu(user_level: str) -> str:
        """Меню поддержки"""
        if user_level == "new":
            return (
                "💬 Центр помощи\n\n"
                "👋 Новичок? Мы поможем разобраться!\n\n"
                "❓ Выберите тему или задайте вопрос"
            )
        elif user_level == "vip":
            return (
                "💬 VIP Поддержка\n\n"
                "👑 Здравствуйте! Рады помочь нашему VIP-клиенту\n\n"
                "🌟 Для вас доступна приоритетная поддержка"
            )
        else:
            return (
                "💬 Центр помощи\n\n"
                "😊 Рады видеть постоянного клиента!\n\n"
                "❓ Выберите тему или свяжитесь с нами напрямую"
            )
    
    @staticmethod
    def how_it_works() -> str:
        """Как работает система"""
        return (
            "💡 Как работает система бонусов\n\n"
            "💰 За каждое посещение получаете кэшбек:\n"
            "• 🥉 Новичок: 5% от суммы\n"
            "• 🥈 Серебро: 7% от суммы\n"
            "• 🥇 Золото: 10% от суммы\n"
            "• 💎 Платина: 15% от суммы\n\n"
            "🎁 Тратить можете на любые услуги до 50% от чека\n\n"
            "📈 Статус повышается автоматически"
        )
    
    @staticmethod
    def contact_info() -> str:
        """Контактная информация"""
        return (
            "📞 Связаться с нами\n\n"
            "🕒 Работаем: пн-пт 9:00-18:00\n"
            "📱 Телефон: +7 (XXX) XXX-XX-XX\n"
            "📧 Email: support@example.com\n\n"
            "💬 Или напишите прямо здесь — отвечаем быстро!"
        )

# ═══════════════════════════════════════════════════════════════════
# ⚠️ ТЕКСТЫ ДЛЯ ОШИБОК И УВЕДОМЛЕНИЙ
# ═══════════════════════════════════════════════════════════════════

class ErrorTexts:
    @staticmethod
    def auth_required() -> str:
        """Требуется авторизация"""
        return (
            "🔐 Нужно войти в систему\n\n"
            "Нажмите /start чтобы авторизоваться"
        )
    
    @staticmethod
    def general_error() -> str:
        """Общая ошибка"""
        return (
            "😔 Что-то пошло не так\n\n"
            "Попробуйте ещё раз или обратитесь в поддержку"
        )
    
    @staticmethod
    def network_error() -> str:
        """Ошибка сети"""
        return (
            "🌐 Проблемы с подключением\n\n"
            "Проверьте интернет и попробуйте снова"
        )
    
    @staticmethod
    def service_unavailable() -> str:
        """Сервис недоступен"""
        return (
            "🔧 Сервис временно недоступен\n\n"
            "Попробуйте через несколько минут"
        )

# ═══════════════════════════════════════════════════════════════════
# 🎮 ТЕКСТЫ ДЛЯ ГЕЙМИФИКАЦИИ
# ═══════════════════════════════════════════════════════════════════

class GamificationTexts:
    @staticmethod
    def new_achievement(achievement: str, reward: int) -> str:
        """Новое достижение"""
        return (
            f"🏆 Новое достижение!\n\n"
            f"'{achievement}'\n\n"
            f"🎁 Награда: +{fmt_money(reward)}\n\n"
            f"Поздравляем! 🎉"
        )
    
    @staticmethod
    def level_up(old_level: str, new_level: str, benefits: List[str]) -> str:
        """Повышение уровня"""
        text = (
            f"🎉 Поздравляем!\n\n"
            f"Ваш статус повышен:\n"
            f"{old_level} → {new_level}\n\n"
            f"🎁 Новые привилегии:\n"
        )
        
        for benefit in benefits:
            text += f"• {benefit}\n"
        
        return text
    
    @staticmethod
    def progress_motivation(current_level: str, progress: float) -> str:
        """Мотивация к прогрессу"""
        if progress > 0.8:
            return f"🔥 До {current_level} статуса остался один шаг!"
        elif progress > 0.5:
            return f"💪 Отличный прогресс к {current_level} статусу!"
        else:
            return f"🚀 Путь к {current_level} статусу начался!"

# ═══════════════════════════════════════════════════════════════════
# 📱 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════

class TextHelpers:
    @staticmethod
    def get_time_greeting() -> str:
        """Приветствие в зависимости от времени суток"""
        from datetime import datetime
        
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
    def format_list(items: List[str], style: str = "bullet") -> str:
        """Форматирование списка"""
        if style == "bullet":
            return "\n".join(f"• {item}" for item in items)
        elif style == "number":
            return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
        else:
            return "\n".join(items)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Обрезка текста с многоточием"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    @staticmethod
    def add_urgency(text: str, urgent: bool = False) -> str:
        """Добавление срочности в текст"""
        if urgent:
            return f"⚡ {text}"
        return text

# ═══════════════════════════════════════════════════════════════════
# 🎨 ЭМОЦИОНАЛЬНАЯ ОКРАСКА ТЕКСТОВ
# ═══════════════════════════════════════════════════════════════════

class EmotionalTone:
    """
    Эмоциональная окраска для разных ситуаций
    """
    
    POSITIVE = {
        "prefix": "🎉",
        "words": ["отлично", "замечательно", "супер", "прекрасно"]
    }
    
    NEUTRAL = {
        "prefix": "ℹ️",
        "words": ["хорошо", "понятно", "ясно", "готово"]
    }
    
    ENCOURAGING = {
        "prefix": "💪",
        "words": ["давайте", "попробуем", "получится", "вперёд"]
    }
    
    HELPFUL = {
        "prefix": "💡",
        "words": ["поможем", "подскажем", "объясним", "покажем"]
    }

# ═══════════════════════════════════════════════════════════════════
# 📊 ШАБЛОНЫ ДЛЯ ПЕРЕМЕННОЙ ИНФОРМАЦИИ
# ═══════════════════════════════════════════════════════════════════

class DynamicTexts:
    @staticmethod
    def balance_with_context(balance: int, last_transaction: str = None) -> str:
        """Баланс с контекстом последней операции"""
        base = f"💰 На счёте: {fmt_money(balance)}"
        
        if last_transaction:
            base += f"\n💫 Последнее: {last_transaction}"
        
        return base
    
    @staticmethod
    def countdown_text(days_left: int, event: str) -> str:
        """Обратный отсчёт до события"""
        if days_left == 0:
            return f"🔥 {event} — сегодня!"
        elif days_left == 1:
            return f"⏰ {event} — завтра"
        else:
            return f"📅 {event} — через {days_left} дн."
    
    @staticmethod
    def percentage_progress(current: int, target: int, unit: str = "₽") -> str:
        """Прогресс в процентах"""
        if target == 0:
            return "100%"
        
        percentage = min(100, (current / target) * 100)
        return f"{percentage:.0f}% ({fmt_money(current)} из {fmt_money(target)})"

# Экспорт основных классов для использования в боте
__all__ = [
    'WelcomeTexts', 'BalanceTexts', 'BookingTexts', 'RedeemTexts',
    'AnalyticsTexts', 'MaintenanceTexts', 'SupportTexts', 'ErrorTexts',
    'GamificationTexts', 'TextHelpers', 'EmotionalTone', 'DynamicTexts'
]
