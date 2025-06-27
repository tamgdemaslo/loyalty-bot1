"""
📝 Минималистичные обработчики
Чистые тексты, минимум эмодзи, максимум пользы
"""

import logging
from aiogram import types, F
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardMarkup, InlineKeyboardBuilder

from bot.db import register_mapping, get_agent_id, get_balance, change_balance, conn
from bot.moysklad import find_agent_by_phone, fetch_shipments, fetch_demand_full
from bot.formatting import fmt_money, fmt_date_local
from bot.accrual import doc_age_seconds, accrue_for_demand
from bot.ux_keyboards import get_user_profile, adaptive_main_menu

# Импорт минималистичных текстов
from ux_copy_texts_minimal import (
    WelcomeTexts, BalanceTexts, BookingTexts, RedeemTexts,
    AnalyticsTexts, MaintenanceTexts, SupportTexts, ErrorTexts,
    GamificationTexts, TextHelpers
)

# Импорт упрощённых умных функций
from bot.smart_features_minimal import (
    PersonalAssistant, SimpleAchievementSystem, SimpleRecommendationEngine
)

log = logging.getLogger(__name__)

# Инициализация упрощённых систем
personal_assistant = PersonalAssistant()
achievement_system = SimpleAchievementSystem()
recommendation_engine = SimpleRecommendationEngine()

class MinimalStates(StatesGroup):
    wait_name = State()
    booking_service = State()
    redeem_amount = State()

def register_minimal_handlers(dp):
    """Регистрация минималистичных обработчиков"""
    
    @dp.message(CommandStart())
    async def minimal_start(m: types.Message):
        """Приветствие без лишних эмодзи"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        user_name = m.from_user.first_name or "друг"
        
        if agent_id:
            # Существующий пользователь
            profile = get_user_profile(m.from_user.id)
            time_greeting = TextHelpers.get_time_greeting()
            
            # Получаем простые рекомендации
            insights = await personal_assistant.get_smart_insights(m.from_user.id)
            
            # Проверяем достижения (без фанфар)
            new_achievements = await achievement_system.check_achievements(m.from_user.id)
            
            message = WelcomeTexts.returning_user(
                name=user_name,
                status=profile['loyalty_level'],
                balance=profile['balance'],
                time_greeting=time_greeting
            )
            
            # Добавляем одну рекомендацию, если есть
            if insights:
                insight = insights[0]
                message += f"\n\n{insight.title}\n{insight.message}"
            
            # Тихо начисляем награды за достижения
            if new_achievements:
                for achievement in new_achievements:
                    change_balance(agent_id, achievement['reward'])
            
            return await m.answer(message, reply_markup=adaptive_main_menu(m.from_user.id))
        
        # Новый пользователь
        kb = ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        
        await m.answer(WelcomeTexts.new_user_greeting(), reply_markup=kb)

    @dp.message(F.content_type == ContentType.CONTACT)
    async def minimal_contact_auth(m: types.Message, state: FSMContext):
        """Авторизация по номеру"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        phone = m.contact.phone_number
        agent_id = find_agent_by_phone(phone)
        user_name = m.from_user.first_name or "друг"

        if agent_id:
            # Регистрируем пользователя
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
                            welcome_bonus_msg = f"\n\nНачислено за последний визит: {fmt_money(added)}"

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
        await state.set_state(MinimalStates.wait_name)
        await state.update_data(phone=phone)
        
        await m.answer(WelcomeTexts.new_client_name_request())

    @dp.message(MinimalStates.wait_name)
    async def minimal_got_name(m: types.Message, state: FSMContext):
        """Получение имени нового клиента"""
        data = await state.get_data()
        phone = data["phone"]
        name = m.text.strip()

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
            await m.answer(ErrorTexts.general_error())
            return

        register_mapping(m.from_user.id, agent_id, phone, name)
        await state.clear()

        await m.answer(WelcomeTexts.profile_created())
        await m.answer("Главное меню", reply_markup=adaptive_main_menu(m.from_user.id))

    @dp.message(F.text.in_(["Баланс", "💎 Баланс"]))
    async def minimal_show_balance(m: types.Message):
        """Показ баланса с простыми рекомендациями"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        profile = get_user_profile(m.from_user.id)
        balance = profile["balance"]
        status = profile["loyalty_level"]
        
        # Выбираем подходящий текст
        if balance == 0:
            message = BalanceTexts.empty_balance(status)
        elif balance < 500:
            message = BalanceTexts.small_balance(balance, status)
        else:
            max_redeem = min(balance, int(balance * 0.3))
            message = BalanceTexts.good_balance(balance, status, max_redeem)

        # Добавляем одну рекомендацию
        insights = await personal_assistant.get_smart_insights(m.from_user.id)
        if insights:
            saving_insights = [i for i in insights if i.type == 'saving']
            if saving_insights:
                insight = saving_insights[0]
                message += f"\n\n{insight.title}\n{insight.message}"

        # Простые кнопки
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="Потратить бонусы", callback_data="redeem_bonuses"))
        kb.row(types.InlineKeyboardButton(text="Как накопить", callback_data="earning_tips"))
        
        await m.answer(message, reply_markup=kb.as_markup())

    @dp.message(F.text.contains("Записаться"))
    async def minimal_booking_start(m: types.Message):
        """Простая запись без излишеств"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        await m.answer(BookingTexts.booking_start())
        
        # Получаем рекомендации
        recommendations = await recommendation_engine.get_recommendations(m.from_user.id)
        
        if recommendations:
            recommended_services = [r['title'] for r in recommendations]
        else:
            recommended_services = ["Замена масла", "Диагностика"]
        
        message = BookingTexts.service_recommendations(recommended_services)
        
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="Выбрать услугу", callback_data="select_service"))
        kb.row(types.InlineKeyboardButton(text="Записаться на диагностику", callback_data="book_diagnostics"))
        
        await m.answer(message, reply_markup=kb.as_markup())

    @dp.message(F.text.contains("Статистика"))
    async def minimal_user_stats(m: types.Message):
        """Простая статистика"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        profile = get_user_profile(m.from_user.id)
        
        # Проверяем достижения без лишнего шума
        new_achievements = await achievement_system.check_achievements(m.from_user.id)
        
        message = AnalyticsTexts.user_stats(
            status=profile['loyalty_level'],
            balance=profile['balance'],
            visits=profile['visits'],
            progress=profile['loyalty_progress']
        )
        
        # Показываем новые достижения спокойно
        if new_achievements:
            message += "\n\nНовые достижения:\n"
            for achievement in new_achievements:
                message += f"• {achievement['title']} (+{achievement['reward']} ₽)\n"
                change_balance(agent_id, achievement['reward'])
        
        await m.answer(message)

    @dp.message(F.text.contains("Списать"))
    async def minimal_redeem_bonuses(m: types.Message):
        """Списание бонусов"""
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
                "service": "ТО",
                "savings": min(balance, 1500),
                "remaining": balance - min(balance, 1500)
            },
            {
                "service": "Запчасти",
                "savings": min(balance, 750),
                "remaining": balance - min(balance, 750)
            },
            {
                "service": "Мойка",
                "savings": min(balance, 500),
                "remaining": balance - min(balance, 500)
            }
        ]
        
        message = RedeemTexts.redeem_scenarios(balance, scenarios)
        
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="Использовать на ТО", callback_data="redeem_to"))
        kb.row(types.InlineKeyboardButton(text="Другие варианты", callback_data="redeem_other"))
        
        await m.answer(message, reply_markup=kb.as_markup())

    @dp.message(F.text.in_(["История посещений", "📊 История", "📊 Моя история"]))
    async def minimal_visit_history(m: types.Message):
        """История посещений со статистикой"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        # Получаем статистику пользователя
        profile = get_user_profile(m.from_user.id)
        
        # Получаем историю из МойСклад
        shipments = fetch_shipments(agent_id, limit=10)
        
        message = AnalyticsTexts.user_stats(
            status=profile['loyalty_level'],
            balance=profile['balance'],
            visits=profile['visits'],
            progress=profile['loyalty_progress']
        )
        
        message += "\n\nПоследние посещения:\n"
        
        if not shipments:
            message += "Пока нет посещений"
        else:
            for i, shipment in enumerate(shipments[:5], 1):
                date_str = fmt_date_local(shipment["moment"])
                amount = shipment.get("sum", 0) / 100  # копейки в рубли
                message += f"{i}. {date_str} \u2022 {fmt_money(amount)}\n"
        
        # Проверяем новые достижения
        new_achievements = await achievement_system.check_achievements(m.from_user.id)
        if new_achievements:
            message += "\n\nНовые достижения:\n"
            for achievement in new_achievements:
                message += f"\u2022 {achievement['title']} (+{achievement['reward']} ₽)\n"
                change_balance(agent_id, achievement['reward'])
        
        await m.answer(message)

    @dp.message(F.text.in_(["Профиль", "👤 Профиль"]))
    async def minimal_user_profile(m: types.Message):
        """Профиль пользователя с достижениями"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())
        
        profile = get_user_profile(m.from_user.id)
        total_spent = 25000  # Временная заглушка
        
        message = (
            f"Профиль\n\n"
            f"Статус: {profile['loyalty_level']}\n"
            f"Бонусы: {fmt_money(profile['balance'])}\n"
            f"Посещений: {profile['visits']}\n"
            f"Telegram: @{m.from_user.username or 'не указан'}\n\n"
        )
        
        # Получаем достижения
        unlocked = achievement_system._get_user_achievements(m.from_user.id)
        all_achievements = achievement_system.achievements
        
        if unlocked:
            message += "Достижения:\n"
            unlocked_rewards = 0
            for achievement_id in unlocked:
                if achievement_id in all_achievements:
                    achievement = all_achievements[achievement_id]
                    message += f"\u2022 {achievement['title']}\n"
                    unlocked_rewards += achievement['reward']
            
            message += f"\nИтого заработано: {unlocked_rewards} ₽"
        else:
            message += "Достижений пока нет"
        
        await m.answer(message)

    @dp.message(F.text.in_(["Связаться", "💬 Поддержка", "📞 Поддержка"]))
    async def minimal_support(m: types.Message):
        """Простая поддержка"""
        profile = get_user_profile(m.from_user.id)
        message = SupportTexts.support_menu(profile["level"])
        
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="Как работают бонусы?", callback_data="system_help"))
        kb.row(types.InlineKeyboardButton(text="Связаться с поддержкой", callback_data="contact_support"))
        
        await m.answer(message, reply_markup=kb.as_markup())

    # Callback обработчики
    @dp.callback_query(F.data == "system_help")
    async def system_help(callback: types.CallbackQuery):
        await callback.message.edit_text(SupportTexts.how_it_works())

    @dp.callback_query(F.data == "contact_support")
    async def contact_support(callback: types.CallbackQuery):
        await callback.message.edit_text(SupportTexts.contact_info())

    @dp.callback_query(F.data == "earning_tips")
    async def earning_tips(callback: types.CallbackQuery):
        message = (
            "Как накопить больше бонусов:\n\n"
            "• Записывайтесь через бот\n"
            "• Посещайте сервис регулярно\n"
            "• Приглашайте друзей\n"
            "• Пользуйтесь дополнительными услугами"
        )
        await callback.message.edit_text(message)

    @dp.callback_query(F.data == "redeem_bonuses")
    async def callback_redeem_bonuses(callback: types.CallbackQuery):
        """Callback для списания бонусов"""
        agent_id = get_agent_id(callback.from_user.id)
        if not agent_id:
            return await callback.answer("Ошибка авторизации")

        balance = get_balance(agent_id)
        
        if balance <= 0:
            return await callback.message.edit_text(RedeemTexts.no_balance())
        
        scenarios = [
            {
                "service": "ТО",
                "savings": min(balance, 1500),
                "remaining": balance - min(balance, 1500)
            },
            {
                "service": "Запчасти",
                "savings": min(balance, 750),
                "remaining": balance - min(balance, 750)
            },
            {
                "service": "Мойка",
                "savings": min(balance, 500),
                "remaining": balance - min(balance, 500)
            }
        ]
        
        message = RedeemTexts.redeem_scenarios(balance, scenarios)
        
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="Использовать на ТО", callback_data="redeem_to"))
        kb.row(types.InlineKeyboardButton(text="Другие варианты", callback_data="redeem_other"))
        
        await callback.message.edit_text(message, reply_markup=kb.as_markup())

    @dp.callback_query(F.data == "redeem_to")
    async def redeem_to_service(callback: types.CallbackQuery):
        """Списание на ТО"""
        await callback.message.edit_text(
            "Для списания бонусов на техническое обслуживание:\n\n"
            "1. Запишитесь на ТО через бот\n"
            "2. При оплате сообщите о желании использовать бонусы\n"
            "3. Скидка будет применена автоматически\n\n"
            "Хотите записаться сейчас?",
            reply_markup=InlineKeyboardBuilder()
            .row(types.InlineKeyboardButton(text="Записаться на ТО", callback_data="book_service"))
            .as_markup()
        )

    @dp.callback_query(F.data == "redeem_other")
    async def redeem_other_options(callback: types.CallbackQuery):
        """Другие варианты списания"""
        await callback.message.edit_text(
            "Варианты использования бонусов:\n\n"
            "• Мойка автомобиля\n"
            "• Покупка автозапчастей\n"
            "• Дополнительные услуги\n"
            "• Диагностика\n\n"
            "Для использования обратитесь к администратору при следующем визите."
        )

    @dp.callback_query(F.data == "show_savings_calculator")
    async def savings_calculator(callback: types.CallbackQuery):
        """Простой калькулятор экономии"""
        profile = get_user_profile(callback.from_user.id)
        balance = profile['balance']
        
        scenarios = [
            {"service": "Замена масла", "cost": 3500, "discount": 30},
            {"service": "Диагностика", "cost": 2000, "discount": 40},
            {"service": "Комплексное ТО", "cost": 8000, "discount": 25},
        ]
        
        message = f"Ваши {balance:,} ₽ бонусов позволяют сэкономить:\n\n"
        
        for scenario in scenarios:
            max_discount = min(balance, int(scenario['cost'] * scenario['discount'] / 100))
            final_cost = scenario['cost'] - max_discount
            message += f"{scenario['service']}\n"
            message += f"Цена: {scenario['cost']:,} ₽\n"
            message += f"Скидка: {max_discount:,} ₽\n"
            message += f"К доплате: {final_cost:,} ₽\n\n"
        
        await callback.message.edit_text(message)

    @dp.message()
    async def handle_unknown_message(m: types.Message):
        """Простая обработка неизвестных сообщений"""
        await m.answer(
            "Не понял команду.\n\n"
            "Используйте кнопки меню для навигации или обратитесь в поддержку."
        )

# Экспорт
__all__ = ['register_minimal_handlers']
