"""
🎯 UX-оптимизированные обработчики событий
Основано на принципах пользовательского опыта и поведенческой психологии
"""

import logging
from datetime import datetime, timedelta
from aiogram import types, F
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardMarkup

# Импорты из основного функционала
from bot.yclients import services, staff, free_slots, book_dates, create_record, format_date_russian
from bot.ux_keyboards import (
    smart_welcome_message, adaptive_main_menu, smart_balance_kb, 
    contextual_notification_kb, gamification_progress_kb, smart_booking_flow_kb,
    onboarding_kb, personalized_support_kb, get_motivational_tip,
    get_user_profile
)
from bot.db import register_mapping, user_contact, get_agent_id, get_balance, change_balance, conn
from bot.config import REDEEM_CAP
from bot.moysklad import find_agent_by_phone, fetch_shipments, fetch_demand_full, apply_discount
from bot.formatting import fmt_money, fmt_date_local, render_positions
from bot.accrual import doc_age_seconds, accrue_for_demand
from bot.loyalty import get_redeem_cap, format_level_status, format_level_benefits, get_level_info, calculate_level_by_spent
from bot.analytics import (
    get_client_statistics, get_client_ranking, get_bonus_history,
    format_client_statistics, format_client_ranking, format_bonus_history
)
from bot.maintenance import (
    get_all_maintenance_status, format_maintenance_summary, format_maintenance_status,
    add_manual_maintenance, MAINTENANCE_WORKS
)

# Настройка логирования
log = logging.getLogger(__name__)

# Состояния для сложных диалогов
class UXStates(StatesGroup):
    wait_name = State()
    onboarding_car_info = State()
    smart_booking_service = State()
    smart_booking_master = State()
    smart_booking_time = State()
    redeem_amount = State()

def register_ux_handlers(dp):
    """Регистрация всех UX-оптимизированных обработчиков"""
    
    # ═══════════════════════════════════════════════════════════════════
    # 🚀 УМНЫЙ СТАРТ И ОНБОРДИНГ
    # ═══════════════════════════════════════════════════════════════════
    
    @dp.message(CommandStart())
    async def ux_cmd_start(m: types.Message):
        """🎯 UX-оптимизированная команда /start"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        user_name = m.from_user.first_name or "друг"
        
        if agent_id:
            # Существующий пользователь - персонализированное приветствие
            message, keyboard = smart_welcome_message(user_name, m.from_user.id)
            
            # Добавляем мотивационный совет
            tip = get_motivational_tip(m.from_user.id)
            message += f"\n\n💡 {tip}"
            
            return await m.answer(message, reply_markup=keyboard)
        
        # Новый пользователь - дружелюбная авторизация
        kb = ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        
        await m.answer(
            "🌟 Добро пожаловать в программу лояльности!\n\n"
            "Здесь вы сможете:\n"
            "• 💰 Получать бонусы за каждое посещение\n"
            "• 📅 Записываться онлайн на обслуживание\n"
            "• 🔧 Отслеживать ТО вашего автомобиля\n"
            "• 🎁 Экономить до 40% с помощью бонусов\n\n"
            "👆 Для начала поделитесь номером телефона:",
            reply_markup=kb
        )

    # ═══════════════════════════════════════════════════════════════════
    # 📱 АВТОРИЗАЦИЯ С УЛУЧШЕННЫМ UX
    # ═══════════════════════════════════════════════════════════════════
    
    @dp.message(F.content_type == ContentType.CONTACT)
    async def ux_contact_auth(m: types.Message, state: FSMContext):
        """📱 UX-оптимизированная авторизация"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        phone = m.contact.phone_number
        agent_id = find_agent_by_phone(phone)
        user_name = m.from_user.first_name or "друг"

        if agent_id:
            # ═══ Существующий клиент ═══
            register_mapping(
                tg_id=m.from_user.id,
                agent_id=agent_id,
                phone=phone,
                fullname=m.contact.first_name or ""
            )

            # Проверяем последние начисления
            last = fetch_shipments(agent_id, limit=1)
            welcome_bonus_msg = ""
            
            if last:
                did = last[0]["id"]
                already = conn.execute(
                    "SELECT 1 FROM accrual_log WHERE demand_id=?", (did,)
                ).fetchone()
                
                if not already:
                    full = fetch_demand_full(did)
                    if doc_age_seconds(full["moment"]) >= 300:
                        added = accrue_for_demand(full)
                        if added:
                            conn.execute(
                                "INSERT INTO accrual_log(demand_id) VALUES(?)", (did,)
                            )
                            conn.commit()
                            welcome_bonus_msg = f"\n\n🎉 Начислено за последнее посещение: {fmt_money(added)}"

            # Персонализированное приветствие для вернувшегося клиента
            profile = get_user_profile(m.from_user.id)
            message = (
                f"✅ С возвращением, {user_name}!\n\n"
                f"🎯 Ваш статус: {profile['loyalty_level']}\n"
                f"💰 Баланс: {fmt_money(profile['balance'])}{welcome_bonus_msg}\n\n"
                f"🚀 Выберите действие:"
            )
            
            await m.answer(message, reply_markup=adaptive_main_menu(m.from_user.id))
            return

        # ═══ Новый клиент - запрашиваем ФИО ═══
        await state.set_state(UXStates.wait_name)
        await state.update_data(phone=phone)
        
        await m.answer(
            "🆕 Вы новый клиент!\n\n"
            "👤 Как к вам обращаться? (ФИО)\n\n"
            "💡 Это поможет нам персонализировать сервис специально для вас"
        )

    @dp.message(UXStates.wait_name)
    async def ux_got_name(m: types.Message, state: FSMContext):
        """👤 Получение ФИО нового клиента"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        data = await state.get_data()
        phone = data["phone"]
        name = m.text.strip()

        # Создание контрагента в МойСклад
        try:
            import requests
            from bot.moysklad import MS_BASE, HEADERS
            
            payload = {
                "name": name,
                "phone": phone,
                "phones": [{"phone": phone}]
            }
            
            resp = requests.post(
                f"{MS_BASE}/counterparty",
                headers=HEADERS,
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            agent_id = resp.json()["id"]

        except Exception as e:
            await m.answer(
                "❌ Не удалось создать профиль клиента\n\n"
                f"Ошибка: {e}\n\n"
                "💬 Обратитесь в поддержку для решения проблемы"
            )
            return

        # Сохранение связи
        register_mapping(m.from_user.id, agent_id, phone, name)
        await state.clear()

        # Приветствие с начислением бонусов
        await m.answer(
            "🎉 Профиль создан!\n\n"
            "💰 Приветственные бонусы: 100 ₽\n"
            "🎯 Ваш стартовый статус: Bronze\n\n"
            "✨ Теперь вы можете зарабатывать бонусы с каждого посещения!"
        )

        # Предлагаем онбординг
        await m.answer(
            "🚀 Хотите настроить профиль?\n\n"
            "Это займет всего 30 секунд и поможет нам:\n"
            "• Отслеживать ТО вашего автомобиля\n"
            "• Напоминать о важных сроках\n"
            "• Предлагать персональные скидки",
            reply_markup=onboarding_kb(1)
        )

    # ═══════════════════════════════════════════════════════════════════
    # 🎯 CALLBACK ОБРАБОТЧИКИ ГЛАВНОГО ИНТЕРФЕЙСА
    # ═══════════════════════════════════════════════════════════════════

    @dp.callback_query(F.data == "continue_chat")
    async def continue_in_chat(callback: types.CallbackQuery):
        """💬 Продолжение работы в чате"""
        await callback.message.edit_text(
            "✅ Отлично! Теперь вы в главном меню.\n\n"
            "💡 Выберите нужное действие из меню ниже:"
        )
        
        await callback.message.answer(
            "🎯 Главное меню", 
            reply_markup=adaptive_main_menu(callback.from_user.id)
        )

    @dp.callback_query(F.data == "onboarding_start")
    async def start_onboarding(callback: types.CallbackQuery):
        """🚀 Начало онбординга"""
        user_name = callback.from_user.first_name or "друг"
        
        await callback.message.edit_text(
            f"👋 Привет, {user_name}!\n\n"
            "Добро пожаловать в нашу программу лояльности! "
            "Давайте настроим ваш профиль за 30 секунд\n\n"
            "Это поможет нам сделать сервис максимально удобным для вас",
            reply_markup=onboarding_kb(1)
        )

    @dp.callback_query(F.data == "onboarding_step_2")
    async def onboarding_step_2(callback: types.CallbackQuery):
        """🚗 Второй шаг онбординга"""
        await callback.message.edit_text(
            "🚗 Расскажите о вашем автомобиле\n\n"
            "Это поможет нам:\n"
            "• 🔧 Отслеживать сроки ТО\n"
            "• ⏰ Напоминать о сервисе\n"
            "• 💡 Предлагать подходящие услуги\n"
            "• 💰 Делать персональные предложения",
            reply_markup=onboarding_kb(2)
        )

    @dp.callback_query(F.data == "onboarding_step_3")
    async def onboarding_step_3(callback: types.CallbackQuery):
        """🎉 Завершение онбординга"""
        await callback.message.edit_text(
            "🎉 Все готово!\n\n"
            "💰 Ваш бонус за регистрацию: 100 ₽\n\n"
            "🎯 Что хотите сделать первым?",
            reply_markup=onboarding_kb(3)
        )

    @dp.callback_query(F.data == "onboarding_skip")
    async def skip_onboarding(callback: types.CallbackQuery):
        """⏭ Пропуск онбординга"""
        await callback.message.edit_text(
            "✅ Понятно! Вы всегда можете настроить профиль позже.\n\n"
            "💡 Для этого используйте кнопку 'Профиль' в главном меню"
        )
        
        await callback.message.answer(
            "🎯 Главное меню",
            reply_markup=adaptive_main_menu(callback.from_user.id)
        )

    @dp.callback_query(F.data == "to_main_menu")
    async def to_main_menu(callback: types.CallbackQuery):
        """🏠 Переход в главное меню"""
        await callback.message.delete()
        
        await callback.message.answer(
            "🎯 Главное меню",
            reply_markup=adaptive_main_menu(callback.from_user.id)
        )

    # ═══════════════════════════════════════════════════════════════════
    # 💰 UX-ОПТИМИЗИРОВАННАЯ РАБОТА С БАЛАНСОМ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["💎 Баланс", "🔥 Рекомендуем"]))
    async def ux_show_balance(m: types.Message):
        """💰 Умный показ баланса с рекомендациями"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer("❌ Необходима авторизация. Используйте /start")

        profile = get_user_profile(m.from_user.id)
        balance = profile["balance"]
        
        # Получаем информацию об уровне лояльности
        total_spent = 25000  # Временная заглушка, в реальности из базы
        level_id = calculate_level_by_spent(total_spent)
        level_info = get_level_info(level_id)
        level_info['level'] = level_info['name']  # Добавляем поле для совместимости
        
        # Персонализированное сообщение в зависимости от баланса
        if balance == 0:
            message = (
                "💳 Ваш бонусный счет\n\n"
                f"💰 Баланс: {fmt_money(balance)}\n"
                f"🎯 Статус: {level_info['level']}\n\n"
                "💡 Как заработать первые бонусы:\n"
                "• 📅 Запишитесь на ТО (+кэшбек)\n"
                "• 👥 Пригласите друга (+500 ₽)\n"
                "• 🔄 Регулярно посещайте сервис\n\n"
                f"📊 {format_level_status(level_info)}"
            )
        elif balance < 500:
            message = (
                "💳 Ваш бонусный счет\n\n"
                f"💰 Баланс: {fmt_money(balance)}\n"
                f"🎯 Статус: {level_info['level']}\n\n"
                "🚀 Накопите еще немного и сможете:\n"
                "• 🎁 Получить скидку на мойку\n"
                "• 💰 Оплатить часть следующего ТО\n\n"
                f"📊 {format_level_status(level_info)}"
            )
        else:
            # Расчет возможной экономии
            max_redeem = min(balance, int(balance * 0.3))  # Максимум 30% для примера
            
            message = (
                "💳 Ваш бонусный счет\n\n"
                f"💰 Баланс: {fmt_money(balance)}\n"
                f"🎯 Статус: {level_info['level']}\n\n"
                "🎁 Вы можете потратить:\n"
                f"• На ТО: до {fmt_money(max_redeem)}\n"
                f"• На запчасти: до {fmt_money(max_redeem)}\n"
                f"• На мойку: {fmt_money(min(balance, 500))}\n\n"
                f"📊 {format_level_status(level_info)}"
            )

        await m.answer(message, reply_markup=smart_balance_kb(m.from_user.id))

    @dp.callback_query(F.data == "spending_recommendations")
    async def spending_recommendations(callback: types.CallbackQuery):
        """💡 Умные рекомендации по тратам"""
        agent_id = get_agent_id(callback.from_user.id)
        if not agent_id:
            return
        
        balance = get_balance(agent_id)
        profile = get_user_profile(callback.from_user.id)
        
        # Генерируем персонализированные рекомендации
        recommendations = []
        
        if balance >= 1000:
            recommendations.append("🔧 Следующее ТО - экономия до 30%")
        if balance >= 500:
            recommendations.append("🛒 Запчасти - экономия до 25%")
        if balance >= 200:
            recommendations.append("🧼 Мойка - полная оплата бонусами")
        if balance >= 100:
            recommendations.append("🔍 Диагностика - частичная оплата")
            
        message = (
            f"💡 Рекомендации для {fmt_money(balance)}\n\n"
            + "\n".join(f"• {rec}" for rec in recommendations) +
            "\n\n💬 Хотите записаться на что-то из перечисленного?"
        )
        
        await callback.message.edit_text(message)

    @dp.callback_query(F.data == "earning_tips")
    async def earning_tips(callback: types.CallbackQuery):
        """💡 Советы по заработку бонусов"""
        profile = get_user_profile(callback.from_user.id)
        
        if profile["level"] == "new":
            tips = [
                "📅 Записывайтесь через бот - получайте двойные бонусы",
                "🔄 Регулярные посещения увеличивают кэшбек",
                "👥 Приглашайте друзей - получайте по 500₽ за каждого"
            ]
        else:
            tips = [
                "🎯 Поднимите статус для большего кэшбека",
                "📈 Увеличивайте чек - больше бонусов",
                "⭐ Оставляйте отзывы - получайте дополнительные бонусы"
            ]
        
        message = (
            "💡 Как заработать больше бонусов:\n\n" +
            "\n".join(f"• {tip}" for tip in tips) +
            "\n\n🚀 Начните прямо сейчас!"
        )
        
        await callback.message.edit_text(message)

    # ═══════════════════════════════════════════════════════════════════
    # 📅 УМНАЯ ЗАПИСЬ НА ОБСЛУЖИВАНИЕ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["📅 Записаться", "📋 Записаться на ТО", "📅 VIP-запись"]))
    async def ux_smart_booking_start(m: types.Message, state: FSMContext):
        """📅 Умное начало записи с рекомендациями"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer("❌ Необходима авторизация. Используйте /start")

        # Имитируем анализ рекомендаций (в реальности - из ТО данных)
        await m.answer("🔍 Подбираем услуги для вас...")
        
        # Получаем рекомендуемые услуги на основе профиля
        profile = get_user_profile(m.from_user.id)
        
        recommendations = []
        if profile["level"] == "new":
            recommendations = ["Диагностика", "Замена масла"]
        else:
            recommendations = ["Замена масла", "Проверка тормозов", "Диагностика подвески"]
        
        message = (
            "🎯 Рекомендуем для вашего авто:\n\n"
            + "\n".join(f"✅ {rec} (пора!)" for rec in recommendations[:2]) +
            "\n" + "\n".join(f"⚠️ {rec} (скоро)" for rec in recommendations[2:]) +
            "\n\n📋 Или выберите из полного каталога услуг:"
        )
        
        context = {"recommended_services": recommendations}
        await state.update_data(context=context)
        await state.set_state(UXStates.smart_booking_service)
        
        await m.answer(
            message,
            reply_markup=smart_booking_flow_kb("service_selection", context)
        )

    @dp.callback_query(F.data == "quick_booking", UXStates.smart_booking_service)
    async def quick_booking_flow(callback: types.CallbackQuery):
        """⚡ Быстрая запись на рекомендуемые услуги"""
        await callback.message.edit_text(
            "⚡ Отлично! Записываем на рекомендуемые услуги.\n\n"
            "🔍 Ищем свободное время у лучших мастеров..."
        )
        
        # Здесь была бы логика поиска времени
        # Пока показываем пример
        await callback.message.edit_text(
            "📅 Найдены свободные слоты:\n\n"
            "⚡ Завтра, 14:00 - Иван М. (ваш мастер) 🌟\n"
            "• Послезавтра, 10:00 - Петр С.\n"
            "• Пятница, 16:00 - Иван М. 🌟\n\n"
            "💡 Иван М. обслуживал вас 3 раза",
            reply_markup=smart_booking_flow_kb("time_selection", {"preferred_master": "Иван М."})
        )

    # ═══════════════════════════════════════════════════════════════════
    # 🎁 УМНОЕ СПИСАНИЕ БОНУСОВ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.contains("Списать"))
    async def ux_smart_redeem(m: types.Message):
        """🎁 Умное списание с визуализацией экономии"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer("❌ Необходима авторизация. Используйте /start")

        balance = get_balance(agent_id)
        
        if balance <= 0:
            return await m.answer(
                "💳 На бонусном счете недостаточно средств\n\n"
                "💡 Заработайте бонусы:\n"
                "• Запишитесь на ТО\n"
                "• Пригласите друга\n"
                "• Регулярно посещайте сервис"
            )
        
        # Рассчитываем варианты использования
        redeem_cap = get_redeem_cap(agent_id)
        max_redeem_pct = min(40, redeem_cap)  # максимум 40%
        
        # Примерные суммы чеков для расчета
        scenarios = [
            {"service": "ТО", "amount": 3500, "icon": "🔧"},
            {"service": "Запчасти", "amount": 2500, "icon": "🛒"},
            {"service": "Мойка", "amount": 800, "icon": "🧼"},
        ]
        
        message = f"💰 Ваши бонусы: {fmt_money(balance)}\n\n🎯 Рекомендуем использовать:\n\n"
        
        for scenario in scenarios:
            max_discount = int(scenario["amount"] * max_redeem_pct / 100)
            can_use = min(balance, max_discount)
            remaining = balance - can_use
            
            message += (
                f"┌─────────────────────────────────┐\n"
                f"│ {scenario['icon']} {scenario['service']:<20} │\n"
                f"│ Экономия: {fmt_money(can_use):<12} ({max_redeem_pct}%) │\n"
                f"│ Останется: {fmt_money(remaining):<11} │\n"
                f"└─────────────────────────────────┘\n\n"
            )
        
        # Добавляем кнопки действий
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        kb = InlineKeyboardBuilder()
        kb.row(
            types.InlineKeyboardButton(text="🎁 Использовать на ТО", callback_data="redeem_to"),
            types.InlineKeyboardButton(text="💳 Другие варианты", callback_data="redeem_other")
        )
        
        await m.answer(message, reply_markup=kb.as_markup())

    # ═══════════════════════════════════════════════════════════════════
    # 💬 ПЕРСОНАЛИЗИРОВАННАЯ ПОДДЕРЖКА
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["💬 Поддержка", "📞 Поддержка"]))
    async def ux_personalized_support(m: types.Message):
        """💬 Персонализированная поддержка"""
        profile = get_user_profile(m.from_user.id)
        
        if profile["level"] == "new":
            message = (
                "💬 Центр поддержки\n\n"
                "👋 Добро пожаловать! Мы поможем вам разобраться:\n"
                "• Как работает система бонусов\n"
                "• Как записаться на обслуживание\n"
                "• Ответим на любые вопросы\n\n"
                "❓ Выберите тему:"
            )
        elif profile["level"] == "vip":
            message = (
                "💬 VIP Поддержка\n\n"
                f"👑 Здравствуйте! Как дела с вашим {profile['loyalty_level']} статусом?\n\n"
                "🌟 Для вас доступна персональная поддержка:\n"
                "• Приоритетная обработка запросов\n"
                "• Прямая связь с менеджером\n"
                "• Эксклюзивные предложения\n\n"
                "❓ Чем можем помочь?"
            )
        else:
            message = (
                "💬 Центр поддержки\n\n"
                "😊 Рады видеть постоянного клиента!\n\n"
                "❓ Выберите нужную тему или свяжитесь с нами напрямую:"
            )
        
        await m.answer(message, reply_markup=personalized_support_kb(m.from_user.id))

    # ═══════════════════════════════════════════════════════════════════
    # 📊 ГЕЙМИФИКАЦИЯ И ДОСТИЖЕНИЯ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["📈 Аналитика", "📈 Статистика", "🏆 Достижения"]))
    async def ux_gamification_stats(m: types.Message):
        """📊 Геймификация и статистика"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer("❌ Необходима авторизация. Используйте /start")

        profile = get_user_profile(m.from_user.id)
        
        # Получаем информацию об уровне лояльности
        total_spent = 25000  # Временная заглушка
        level_id = calculate_level_by_spent(total_spent)
        level_info = get_level_info(level_id)
        level_info['level'] = level_info['name']
        
        # Прогресс к следующему уровню
        progress = profile.get("loyalty_progress", 0)
        
        message = (
            f"📊 Ваша статистика\n\n"
            f"🎯 Текущий статус: {level_info['level']}\n"
            f"💰 Баланс: {fmt_money(profile['balance'])}\n"
            f"🏃‍♂️ Посещений: {profile['visits']}\n\n"
            f"📈 Прогресс до следующего уровня:\n"
            f"{'▓' * int(progress * 10)}{'░' * (10 - int(progress * 10))} {progress:.0%}\n\n"
        )
        
        # Добавляем мотивационные элементы
        if progress > 0.8:
            message += "🔥 Финальный рывок! Совсем немного до повышения!\n\n"
        elif progress > 0.5:
            message += "🚀 Отличный прогресс! Продолжайте в том же духе!\n\n"
        else:
            message += "💪 Хорошее начало! Впереди много интересного!\n\n"
        
        # Достижения (примерные)
        achievements = []
        if profile["visits"] >= 1:
            achievements.append("🏆 Первый визит")
        if profile["visits"] >= 5:
            achievements.append("🌟 Постоянный клиент")
        if profile["balance"] >= 1000:
            achievements.append("💎 Накопитель")
        
        if achievements:
            message += f"🏆 Ваши достижения:\n" + "\n".join(f"• {ach}" for ach in achievements)
        
        await m.answer(
            message, 
            reply_markup=gamification_progress_kb(level_info['level'], progress)
        )

    # ═══════════════════════════════════════════════════════════════════
    # 🔧 ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (упрощенные версии)
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["🔧 ТО", "🛠 ТО статус"]))
    async def ux_maintenance_status(m: types.Message):
        """🔧 Статус технического обслуживания"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer("❌ Необходима авторизация")

        status = get_all_maintenance_status(agent_id)
        summary = format_maintenance_summary(status)
        
        message = (
            "🔧 Статус ТО вашего автомобиля\n\n"
            f"{summary}\n\n"
            "💡 Нажмите на пункт для подробной информации"
        )
        
        await m.answer(message)

    @dp.message(F.text.in_(["👤 Профиль"]))
    async def ux_user_profile(m: types.Message):
        """👤 Профиль пользователя"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer("❌ Необходима авторизация")
        
        profile = get_user_profile(m.from_user.id)
        
        # Получаем информацию об уровне лояльности
        total_spent = 25000  # Временная заглушка
        level_id = calculate_level_by_spent(total_spent)
        level_info = get_level_info(level_id)
        level_info['level'] = level_info['name']
        
        message = (
            f"👤 Ваш профиль\n\n"
            f"🎯 Статус: {level_info['level']}\n"
            f"💰 Баланс: {fmt_money(profile['balance'])}\n"
            f"🏃‍♂️ Посещений: {profile['visits']}\n"
            f"📱 Telegram: @{m.from_user.username or 'не указан'}\n\n"
            f"📊 {format_level_status(level_id, total_spent)}"
        )
        
        from bot.keyboards import profile_menu_kb
        await m.answer(message, reply_markup=profile_menu_kb())

    @dp.message(F.text.in_(["📊 История", "📊 Моя история"]))
    async def ux_visit_history(m: types.Message):
        """📊 История посещений"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer("❌ Необходима авторизация")

        # Получаем историю из МойСклад
        shipments = fetch_shipments(agent_id, limit=10)
        
        if not shipments:
            return await m.answer(
                "📊 История посещений\n\n"
                "🤷‍♂️ Пока нет записей о посещениях.\n\n"
                "💡 После первого визита здесь появится история ваших покупок и услуг."
            )
        
        message = "📊 Ваши последние посещения:\n\n"
        
        for i, shipment in enumerate(shipments[:5], 1):
            date_str = fmt_date_local(shipment["moment"])
            amount = shipment.get("sum", 0) / 100  # переводим копейки в рубли
            message += f"{i}. {date_str} • {fmt_money(amount)}\n"
        
        if len(shipments) > 5:
            message += f"\n... и еще {len(shipments) - 5} посещений"
        
        from bot.handlers import list_visits_kb
        await m.answer(message, reply_markup=list_visits_kb(shipments))

    # ═══════════════════════════════════════════════════════════════════
    # 💡 ПОМОЩЬ И ОБУЧЕНИЕ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["💡 Как работают бонусы?"]))
    async def ux_bonus_help(m: types.Message):
        """💡 Объяснение системы бонусов"""
        profile = get_user_profile(m.from_user.id)
        
        message = (
            "💡 Как работает система бонусов\n\n"
            "💰 За каждое посещение вы получаете кэшбек:\n"
            "• 🥉 Bronze: 3% от суммы чека\n"
            "• 🥈 Silver: 4% от суммы чека\n"
            "• 🥇 Gold: 5% от суммы чека\n"
            "• 💎 Platinum: 6% от суммы чека\n"
            "• 👑 VIP: 7% от суммы чека\n\n"
            "🎁 Тратить бонусы можно:\n"
            f"• До {profile.get('loyalty_level', 'Bronze')} уровня: до 30% от чека\n"
            "• На любые услуги и запчасти\n"
            "• В любое время\n\n"
            "📈 Повышение статуса зависит от потраченной суммы"
        )
        
        await m.answer(message)
