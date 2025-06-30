"""
📝 Обработчики с улучшенными UX-текстами
Применение принципов UX-копирайтинга для максимально понятного интерфейса
"""

import logging
from datetime import datetime, timedelta
from aiogram import types, F
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardMarkup

# Импорты основного функционала
from bot.yclients import services, staff, free_slots, book_dates, create_record, format_date_russian
from bot.ux_keyboards import (
    smart_welcome_message, adaptive_main_menu, smart_balance_kb,
    personalized_support_kb, contextual_notification_kb
)
from bot.smart_features import (
    PersonalAssistant, AchievementSystem, SmartNotificationSystem,
    RecommendationEngine, SmartAnalytics
)
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

# Импорт улучшенных текстов
from ux_copy_texts import (
    WelcomeTexts, BalanceTexts, BookingTexts, RedeemTexts,
    AnalyticsTexts, MaintenanceTexts, SupportTexts, ErrorTexts,
    GamificationTexts, TextHelpers, EmotionalTone, DynamicTexts
)

# Настройка логирования
log = logging.getLogger(__name__)

# Состояния для сложных диалогов
class UXCopyStates(StatesGroup):
    wait_name = State()
    onboarding_car_info = State()
    smart_booking_service = State()
    smart_booking_master = State()
    smart_booking_time = State()
    redeem_amount = State()

def register_ux_copy_handlers(dp):
    """Регистрация обработчиков с улучшенными UX-текстами"""
    
    # ═══════════════════════════════════════════════════════════════════
    # 🚀 ПРИВЕТСТВИЕ С УЛУЧШЕННЫМИ ТЕКСТАМИ
    # ═══════════════════════════════════════════════════════════════════
    
    @dp.message(CommandStart())
    async def ux_copy_start(m: types.Message):
        """🎯 Команда /start с улучшенными текстами"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        user_name = m.from_user.first_name or "друг"
        
        if agent_id:
            # Существующий пользователь
            profile = get_user_profile(m.from_user.id)
            time_greeting = TextHelpers.get_time_greeting()
            
            message = WelcomeTexts.returning_user(
                name=user_name,
                status=profile['loyalty_level'],
                balance=profile['balance'],
                time_greeting=time_greeting
            )
            
            # Добавляем мотивационный совет
            tip = get_motivational_tip(m.from_user.id)
            message += f"\n\n💡 {tip}"
            
            message, keyboard = smart_welcome_message(user_name, m.from_user.id)
            return await m.answer(message, reply_markup=keyboard)
        
        # Новый пользователь
        kb = ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        
        await m.answer(
            WelcomeTexts.new_user_greeting(),
            reply_markup=kb
        )

    # ═══════════════════════════════════════════════════════════════════
    # 📱 АВТОРИЗАЦИЯ С ЧЕЛОВЕЧНЫМИ ТЕКСТАМИ
    # ═══════════════════════════════════════════════════════════════════
    
    @dp.message(F.content_type == ContentType.CONTACT)
    async def ux_copy_contact_auth(m: types.Message, state: FSMContext):
        """📱 Авторизация с улучшенными текстами"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        phone = m.contact.phone_number
        agent_id = find_agent_by_phone(phone)
        user_name = m.from_user.first_name or "друг"

        if agent_id:
            # Существующий клиент
            register_mapping(
                tg_id=m.from_user.id,
                agent_id=agent_id,
                phone=phone,
                fullname=m.contact.first_name or ""
            )

            # Проверяем бонусы за последнее посещение
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
                            welcome_bonus_msg = f"\n\n🎉 Начислено за последний визит: {fmt_money(added)}"

            # Используем улучшенный текст приветствия
            profile = get_user_profile(m.from_user.id)
            time_greeting = TextHelpers.get_time_greeting()
            
            message = WelcomeTexts.returning_user(
                name=user_name,
                status=profile['loyalty_level'],
                balance=profile['balance'],
                time_greeting=time_greeting
            )
            message += welcome_bonus_msg
            
            await m.answer(message, reply_markup=adaptive_main_menu(m.from_user.id))
            return

        # Новый клиент
        await state.set_state(UXCopyStates.wait_name)
        await state.update_data(phone=phone)
        
        await m.answer(WelcomeTexts.new_client_name_request())

    @dp.message(UXCopyStates.wait_name)
    async def ux_copy_got_name(m: types.Message, state: FSMContext):
        """👤 Получение имени с дружелюбным подтверждением"""
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
                ErrorTexts.general_error() + 
                f"\n\n🔧 Техническая информация: {e}\n\n" +
                "💬 Обратитесь в поддержку — мы быстро всё исправим!"
            )
            return

        # Сохранение связи
        register_mapping(m.from_user.id, agent_id, phone, name)
        await state.clear()

        # Подтверждение создания профиля
        await m.answer(WelcomeTexts.profile_created())

        # Предлагаем онбординг
        await m.answer(
            WelcomeTexts.onboarding_offer(),
            reply_markup=onboarding_kb(1)
        )

    # ═══════════════════════════════════════════════════════════════════
    # 🎯 CALLBACK ОБРАБОТЧИКИ С ПОНЯТНЫМИ ТЕКСТАМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.callback_query(F.data == "continue_chat")
    async def continue_in_chat(callback: types.CallbackQuery):
        """💬 Продолжение в чате"""
        await callback.message.edit_text(
            "✅ Отлично! Теперь главное меню у вас под рукой\n\n"
            "👇 Выберите что нужно из кнопок ниже"
        )
        
        await callback.message.answer(
            "🎯 Главное меню", 
            reply_markup=adaptive_main_menu(callback.from_user.id)
        )

    @dp.callback_query(F.data == "onboarding_start")
    async def start_onboarding(callback: types.CallbackQuery):
        """🚀 Начало онбординга с дружелюбным тоном"""
        user_name = callback.from_user.first_name or "друг"
        
        await callback.message.edit_text(
            f"👋 Привет, {user_name}!\n\n"
            "Давайте быстро настроим всё под вас.\n"
            "Это займёт буквально полминуты, но сделает пользование намного удобнее!",
            reply_markup=onboarding_kb(1)
        )

    @dp.callback_query(F.data == "onboarding_step_2")
    async def onboarding_step_2(callback: types.CallbackQuery):
        """🚗 Второй шаг онбординга"""
        await callback.message.edit_text(
            WelcomeTexts.onboarding_offer(),
            reply_markup=onboarding_kb(2)
        )

    @dp.callback_query(F.data == "onboarding_step_3")
    async def onboarding_step_3(callback: types.CallbackQuery):
        """🎉 Завершение онбординга"""
        await callback.message.edit_text(
            WelcomeTexts.onboarding_complete(),
            reply_markup=onboarding_kb(3)
        )

    @dp.callback_query(F.data == "onboarding_skip")
    async def skip_onboarding(callback: types.CallbackQuery):
        """⏭ Пропуск онбординга без давления"""
        await callback.message.edit_text(WelcomeTexts.onboarding_skip())
        
        await callback.message.answer(
            "🎯 Главное меню",
            reply_markup=adaptive_main_menu(callback.from_user.id)
        )

    @dp.callback_query(F.data == "to_main_menu")
    async def to_main_menu(callback: types.CallbackQuery):
        """🏠 Переход в главное меню"""
        await callback.message.delete()
        
        await callback.message.answer(
            "🏠 Вы в главном меню",
            reply_markup=adaptive_main_menu(callback.from_user.id)
        )

    # ═══════════════════════════════════════════════════════════════════
    # 💰 БАЛАНС С ПОНЯТНЫМИ ОБЪЯСНЕНИЯМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["💎 Баланс", "🔥 Рекомендуем"]))
    async def ux_copy_show_balance(m: types.Message):
        """💰 Показ баланса с человечными текстами"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        profile = get_user_profile(m.from_user.id)
        balance = profile["balance"]
        status = profile["loyalty_level"]
        
        # Выбираем подходящий текст в зависимости от баланса
        if balance == 0:
            message = BalanceTexts.empty_balance(status)
        elif balance < 500:
            message = BalanceTexts.small_balance(balance, status)
        else:
            max_redeem = min(balance, int(balance * 0.3))
            message = BalanceTexts.good_balance(balance, status, max_redeem)

        await m.answer(message, reply_markup=smart_balance_kb(m.from_user.id))

    @dp.callback_query(F.data == "spending_recommendations")
    async def spending_recommendations(callback: types.CallbackQuery):
        """💡 Рекомендации по тратам с конкретными цифрами"""
        agent_id = get_agent_id(callback.from_user.id)
        if not agent_id:
            return
        
        balance = get_balance(agent_id)
        message = BalanceTexts.spending_recommendations(balance)
        
        await callback.message.edit_text(message)

    @dp.callback_query(F.data == "earning_tips")
    async def earning_tips(callback: types.CallbackQuery):
        """💡 Советы по заработку с мотивацией"""
        profile = get_user_profile(callback.from_user.id)
        message = BalanceTexts.earning_tips(profile["level"])
        
        await callback.message.edit_text(message)

    # ═══════════════════════════════════════════════════════════════════
    # 📅 ЗАПИСЬ С ПРОСТЫМИ ОБЪЯСНЕНИЯМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["📅 Записаться", "📋 Записаться на ТО", "📅 VIP-запись"]))
    async def ux_copy_booking_start(m: types.Message, state: FSMContext):
        """📅 Начало записи с понятными шагами"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        # Показываем что происходит
        await m.answer(BookingTexts.booking_start())
        
        # Получаем рекомендации для пользователя
        profile = get_user_profile(m.from_user.id)
        
        recommendations = []
        if profile["level"] == "new":
            recommendations = ["Диагностика", "Замена масла"]
        else:
            recommendations = ["Замена масла", "Проверка тормозов", "Диагностика подвески"]
        
        message = BookingTexts.service_recommendations(recommendations)
        
        context = {"recommended_services": recommendations}
        await state.update_data(context=context)
        await state.set_state(UXCopyStates.smart_booking_service)
        
        await m.answer(
            message,
            reply_markup=smart_booking_flow_kb("service_selection", context)
        )

    @dp.callback_query(F.data == "quick_booking", UXCopyStates.smart_booking_service)
    async def quick_booking_flow(callback: types.CallbackQuery):
        """⚡ Быстрая запись с понятным процессом"""
        await callback.message.edit_text(
            "⚡ Отлично! Запишем вас на рекомендуемые услуги\n\n"
            "🔍 Ищем свободного мастера в ближайшее время..."
        )
        
        # Имитация поиска времени
        await callback.message.edit_text(
            BookingTexts.master_selection("Иван Михайлов") + "\n\n" +
            BookingTexts.time_selection(),
            reply_markup=smart_booking_flow_kb("time_selection", {"preferred_master": "Иван М."})
        )

    # ═══════════════════════════════════════════════════════════════════
    # 🎁 СПИСАНИЕ БОНУСОВ С ВИЗУАЛИЗАЦИЕЙ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.contains("Списать"))
    async def ux_copy_redeem_bonuses(m: types.Message):
        """🎁 Списание бонусов с понятными сценариями"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        balance = get_balance(agent_id)
        
        if balance <= 0:
            return await m.answer(RedeemTexts.no_balance())
        
        # Создаем сценарии использования
        scenarios = [
            {
                "icon": "🔧",
                "service": "ТО",
                "savings": min(balance, 1050),
                "percent": 30,
                "remaining": balance - min(balance, 1050)
            },
            {
                "icon": "🛒", 
                "service": "Запчасти",
                "savings": min(balance, 750),
                "percent": 25,
                "remaining": balance - min(balance, 750)
            },
            {
                "icon": "🧼",
                "service": "Мойка",
                "savings": min(balance, 500),
                "percent": 100,
                "remaining": balance - min(balance, 500)
            }
        ]
        
        message = RedeemTexts.redeem_scenarios(balance, scenarios)
        
        # Добавляем кнопки действий
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        kb = InlineKeyboardBuilder()
        kb.row(
            types.InlineKeyboardButton(text="🔧 Использовать на ТО", callback_data="redeem_to"),
            types.InlineKeyboardButton(text="💳 Другие варианты", callback_data="redeem_other")
        )
        
        await m.answer(message, reply_markup=kb.as_markup())

    # ═══════════════════════════════════════════════════════════════════
    # 📊 СТАТИСТИКА С МОТИВИРУЮЩИМИ ТЕКСТАМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["📈 Аналитика", "📈 Статистика", "🏆 Достижения"]))
    async def ux_copy_user_stats(m: types.Message):
        """📊 Статистика с мотивирующими элементами"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        profile = get_user_profile(m.from_user.id)
        
        message = AnalyticsTexts.user_stats(
            status=profile['loyalty_level'],
            balance=profile['balance'],
            visits=profile['visits'],
            progress=profile['loyalty_progress']
        )
        
        # Достижения (примерные)
        achievements = []
        if profile["visits"] >= 1:
            achievements.append("🏆 Первый визит")
        if profile["visits"] >= 5:
            achievements.append("🌟 Постоянный клиент")
        if profile["balance"] >= 1000:
            achievements.append("💎 Накопитель")
        
        if achievements:
            message += f"\n\n{AnalyticsTexts.achievements(achievements)}"
        
        await m.answer(
            message, 
            reply_markup=gamification_progress_kb(profile['loyalty_level'], profile['loyalty_progress'])
        )

    # ═══════════════════════════════════════════════════════════════════
    # 🔧 ТЕХОБСЛУЖИВАНИЕ С ПОНЯТНЫМИ СТАТУСАМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["🔧 ТО", "🛠 ТО статус"]))
    async def ux_copy_maintenance_status(m: types.Message):
        """🔧 Статус ТО с понятными объяснениями"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        status = get_all_maintenance_status(agent_id)
        summary = format_maintenance_summary(status)
        
        message = (
            MaintenanceTexts.maintenance_overview() + 
            f"\n\n{summary}\n\n" +
            "💡 Нажмите на любой пункт для подробностей"
        )
        
        await m.answer(message)

    # ═══════════════════════════════════════════════════════════════════
    # 👤 ПРОФИЛЬ С ДРУЖЕЛЮБНОЙ ПОДАЧЕЙ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["👤 Профиль"]))
    async def ux_copy_user_profile(m: types.Message):
        """👤 Профиль с человечной подачей информации"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())
        
        profile = get_user_profile(m.from_user.id)
        total_spent = 25000  # Временная заглушка
        level_id = calculate_level_by_spent(total_spent)
        
        message = (
            f"👤 Ваш профиль\n\n"
            f"🎯 Статус: {profile['loyalty_level']}\n"
            f"💰 Бонусы: {fmt_money(profile['balance'])}\n"
            f"🏃‍♂️ Посещений: {profile['visits']}\n"
            f"📱 Telegram: @{m.from_user.username or 'не указан'}\n\n"
            f"📊 {format_level_status(level_id, total_spent)}"
        )
        
        from bot.keyboards import profile_menu_kb
        await m.answer(message, reply_markup=profile_menu_kb())

    # ═══════════════════════════════════════════════════════════════════
    # 📊 ИСТОРИЯ С ПОНЯТНОЙ ПОДАЧЕЙ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["📊 История", "📊 Моя история"]))
    async def ux_copy_visit_history(m: types.Message):
        """📊 История с дружелюбным тоном"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        # Получаем историю из МойСклад
        shipments = fetch_shipments(agent_id, limit=10)
        
        if not shipments:
            return await m.answer(AnalyticsTexts.visit_history_empty())
        
        message = "📊 Ваши последние визиты:\n\n"
        
        for i, shipment in enumerate(shipments[:5], 1):
            date_str = fmt_date_local(shipment["moment"])
            amount = shipment.get("sum", 0) / 100  # переводим копейки в рубли
            message += f"{i}. {date_str} • {fmt_money(amount)}\n"
        
        if len(shipments) > 5:
            message += f"\n📋 ...и ещё {len(shipments) - 5} посещений"
        
        message += "\n\n💡 Нажмите на любой визит для подробностей"
        
        from bot.handlers import list_visits_kb
        await m.answer(message, reply_markup=list_visits_kb(shipments))

    # ═══════════════════════════════════════════════════════════════════
    # 💬 ПОДДЕРЖКА С ПЕРСОНАЛИЗАЦИЕЙ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["💬 Поддержка", "📞 Поддержка"]))
    async def ux_copy_support(m: types.Message):
        """💬 Поддержка с учетом уровня пользователя"""
        profile = get_user_profile(m.from_user.id)
        
        message = SupportTexts.support_menu(profile["level"])
        
        await m.answer(message, reply_markup=personalized_support_kb(m.from_user.id))

    # ═══════════════════════════════════════════════════════════════════
    # 💡 ПОМОЩЬ И ОБУЧЕНИЕ С ПРОСТЫМИ ОБЪЯСНЕНИЯМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["💡 Как работают бонусы?"]))
    async def ux_copy_bonus_help(m: types.Message):
        """💡 Объяснение бонусов простым языком"""
        await m.answer(SupportTexts.how_it_works())

    @dp.callback_query(F.data == "system_help")
    async def system_help(callback: types.CallbackQuery):
        """❓ Помощь по системе"""
        await callback.message.edit_text(SupportTexts.how_it_works())

    @dp.callback_query(F.data == "contact_support")
    async def contact_support(callback: types.CallbackQuery):
        """📞 Контактная информация"""
        await callback.message.edit_text(SupportTexts.contact_info())

    # ═══════════════════════════════════════════════════════════════════
    # 🎮 ГЕЙМИФИКАЦИЯ С МОТИВИРУЮЩИМИ ТЕКСТАМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.callback_query(F.data == "show_achievements")
    async def show_achievements(callback: types.CallbackQuery):
        """🏆 Показ достижений с мотивацией"""
        profile = get_user_profile(callback.from_user.id)
        
        # Примерные достижения
        achievements = []
        if profile["visits"] >= 1:
            achievements.append("🏆 Первый шаг — первое посещение")
        if profile["visits"] >= 5:
            achievements.append("🌟 Завсегдатай — 5 посещений")
        if profile["balance"] >= 1000:
            achievements.append("💎 Копилка — накопили 1000₽")
        
        message = AnalyticsTexts.achievements(achievements)
        
        await callback.message.edit_text(message)

    @dp.callback_query(F.data == "action_plan")
    async def action_plan(callback: types.CallbackQuery):
        """🎯 План действий для повышения статуса"""
        profile = get_user_profile(callback.from_user.id)
        
        if profile["loyalty_progress"] > 0.8:
            tips = [
                "🔧 Запишитесь на плановое ТО",
                "🛒 Купите необходимые запчасти", 
                "🧼 Сделайте комплексную мойку"
            ]
            message = "🔥 До повышения статуса — один шаг!\n\nВаш план:\n"
        else:
            tips = [
                "📅 Записывайтесь через бот — больше бонусов",
                "🔄 Посещайте сервис регулярно",
                "👥 Приглашайте друзей — получайте награды"
            ]
            message = "🚀 План повышения статуса:\n\n"
        
        message += TextHelpers.format_list(tips)
        message += "\n\n💪 Каждый шаг приближает вас к цели!"
        
        await callback.message.edit_text(message)

    # ═══════════════════════════════════════════════════════════════════
    # ⚠️ ОБРАБОТКА ОШИБОК С ЧЕЛОВЕЧНЫМИ СООБЩЕНИЯМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message()
    async def handle_unknown_message(m: types.Message):
        """🤷‍♂️ Обработка неизвестных сообщений"""
        await m.answer(
            "🤔 Не совсем понял, что вы хотели\n\n"
            "💡 Воспользуйтесь кнопками меню — так проще!\n\n"
            "🆘 Если нужна помощь, нажмите 'Поддержка'"
        )

# Экспорт функции регистрации
__all__ = ['register_ux_copy_handlers']
