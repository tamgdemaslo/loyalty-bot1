"""
🧠 Обработчики с интеграцией умных функций
Персональный помощник, достижения, уведомления и аналитика
"""

import logging
from datetime import datetime, timedelta
from aiogram import types, F
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardMarkup, InlineKeyboardBuilder

# Импорты основного функционала
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

# Импорт улучшенных текстов
from ux_copy_texts import (
    WelcomeTexts, BalanceTexts, BookingTexts, RedeemTexts,
    AnalyticsTexts, MaintenanceTexts, SupportTexts, ErrorTexts,
    GamificationTexts, TextHelpers, EmotionalTone, DynamicTexts
)

# Импорт умных функций
from bot.smart_features import (
    PersonalAssistant, AchievementSystem, SmartNotificationSystem,
    RecommendationEngine, SmartAnalytics
)

# Настройка логирования
log = logging.getLogger(__name__)

# Инициализация умных систем
personal_assistant = PersonalAssistant()
achievement_system = AchievementSystem()
recommendation_engine = RecommendationEngine()
smart_analytics = SmartAnalytics()

# Состояния для сложных диалогов
class SmartStates(StatesGroup):
    wait_name = State()
    onboarding_car_info = State()
    smart_booking_service = State()
    smart_booking_master = State()
    smart_booking_time = State()
    redeem_amount = State()

def register_smart_handlers(dp):
    """Регистрация обработчиков с умными функциями"""
    
    # ═══════════════════════════════════════════════════════════════════
    # 🚀 ПРИВЕТСТВИЕ С ПЕРСОНАЛЬНЫМ ПОМОЩНИКОМ
    # ═══════════════════════════════════════════════════════════════════
    
    @dp.message(CommandStart())
    async def smart_start(m: types.Message):
        """🎯 Команда /start с умными рекомендациями"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        user_name = m.from_user.first_name or "друг"
        
        if agent_id:
            # Существующий пользователь - показываем умные инсайты
            profile = get_user_profile(m.from_user.id)
            time_greeting = TextHelpers.get_time_greeting()
            
            # Получаем персональные рекомендации
            insights = await personal_assistant.get_smart_insights(m.from_user.id)
            
            # Проверяем новые достижения
            new_achievements = await achievement_system.check_achievements(m.from_user.id)
            
            message = WelcomeTexts.returning_user(
                name=user_name,
                status=profile['loyalty_level'],
                balance=profile['balance'],
                time_greeting=time_greeting
            )
            
            # Добавляем умные рекомендации
            if insights:
                top_insight = insights[0]
                message += f"\n\n{top_insight.emoji} {top_insight.title}\n{top_insight.message}"
            
            # Уведомляем о новых достижениях
            if new_achievements:
                achievement = new_achievements[0]
                message += f"\n\n🎉 Новое достижение: {achievement.title}!\n💰 +{achievement.reward} бонусов"
                # Начисляем награду
                change_balance(agent_id, achievement.reward)
            
            # Добавляем мотивационный совет
            tip = get_motivational_tip(m.from_user.id)
            message += f"\n\n💡 {tip}"
            
            return await m.answer(message, reply_markup=adaptive_main_menu(m.from_user.id))
        
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
    # 📱 АВТОРИЗАЦИЯ С УМНЫМИ УВЕДОМЛЕНИЯМИ
    # ═══════════════════════════════════════════════════════════════════
    
    @dp.message(F.content_type == ContentType.CONTACT)
    async def smart_contact_auth(m: types.Message, state: FSMContext):
        """📱 Авторизация с персональными уведомлениями"""
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
            
            # Получаем персональные рекомендации
            insights = await personal_assistant.get_smart_insights(m.from_user.id)
            
            message = WelcomeTexts.returning_user(
                name=user_name,
                status=profile['loyalty_level'],
                balance=profile['balance'],
                time_greeting=time_greeting
            )
            message += welcome_bonus_msg
            
            # Добавляем топ рекомендацию
            if insights:
                top_insight = insights[0]
                message += f"\n\n{top_insight.emoji} {top_insight.title}\n{top_insight.message}"
            
            await m.answer(message, reply_markup=adaptive_main_menu(m.from_user.id))
            return

        # Новый клиент
        await state.set_state(SmartStates.wait_name)
        await state.update_data(phone=phone)
        
        await m.answer(WelcomeTexts.new_client_name_request())

    @dp.message(SmartStates.wait_name)
    async def smart_got_name(m: types.Message, state: FSMContext):
        """👤 Получение имени с умным онбордингом"""
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

        # Предлагаем умный онбординг
        await m.answer(
            WelcomeTexts.onboarding_offer(),
            reply_markup=onboarding_kb(1)
        )

    # ═══════════════════════════════════════════════════════════════════
    # 💰 БАЛАНС С УМНЫМИ РЕКОМЕНДАЦИЯМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["💎 Баланс", "🔥 Рекомендуем"]))
    async def smart_show_balance(m: types.Message):
        """💰 Показ баланса с персональными рекомендациями"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        profile = get_user_profile(m.from_user.id)
        balance = profile["balance"]
        status = profile["loyalty_level"]
        
        # Получаем персональные рекомендации
        recommendations = await recommendation_engine.get_personalized_recommendations(m.from_user.id)
        
        # Выбираем подходящий текст в зависимости от баланса
        if balance == 0:
            message = BalanceTexts.empty_balance(status)
        elif balance < 500:
            message = BalanceTexts.small_balance(balance, status)
        else:
            max_redeem = min(balance, int(balance * 0.3))
            message = BalanceTexts.good_balance(balance, status, max_redeem)

        # Добавляем персональные рекомендации
        if recommendations:
            financial_recs = [r for r in recommendations if r['type'] == 'financial']
            if financial_recs:
                rec = financial_recs[0]
                message += f"\n\n💡 {rec['title']}\n{rec['description']}"

        await m.answer(message, reply_markup=smart_balance_kb(m.from_user.id))

    @dp.callback_query(F.data == "smart_insights")
    async def show_smart_insights(callback: types.CallbackQuery):
        """🧠 Показ умных инсайтов"""
        insights = await personal_assistant.get_smart_insights(callback.from_user.id)
        
        if not insights:
            await callback.answer("Пока нет персональных рекомендаций")
            return
        
        message = "🧠 Персональные рекомендации:\n\n"
        
        for i, insight in enumerate(insights, 1):
            message += f"{i}. {insight.emoji} {insight.title}\n"
            message += f"   {insight.message}\n\n"
        
        # Создаем кнопки для действий
        kb = InlineKeyboardBuilder()
        for insight in insights[:2]:  # Показываем кнопки для первых двух рекомендаций
            kb.row(types.InlineKeyboardButton(
                text=insight.action_text, 
                callback_data=insight.action_data
            ))
        
        await callback.message.edit_text(message, reply_markup=kb.as_markup())

    # ═══════════════════════════════════════════════════════════════════
    # 📅 УМНАЯ ЗАПИСЬ С РЕКОМЕНДАЦИЯМИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["📅 Записаться", "📋 Записаться на ТО", "📅 VIP-запись"]))
    async def smart_booking_start(m: types.Message, state: FSMContext):
        """📅 Начало записи с умными рекомендациями"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        # Показываем что происходит
        await m.answer(BookingTexts.booking_start())
        
        # Получаем персональные рекомендации по услугам
        recommendations = await recommendation_engine.get_personalized_recommendations(m.from_user.id)
        service_recs = [r for r in recommendations if r['type'] == 'service']
        
        profile = get_user_profile(m.from_user.id)
        
        # Формируем рекомендации
        if service_recs:
            recommended_services = [r['title'].replace('🔧 ', '').replace('🧼 ', '') for r in service_recs]
        elif profile["level"] == "new":
            recommended_services = ["Диагностика", "Замена масла"]
        else:
            recommended_services = ["Замена масла", "Проверка тормозов", "Диагностика подвески"]
        
        message = BookingTexts.service_recommendations(recommended_services)
        
        # Добавляем рекомендации по времени
        behavior = await smart_analytics.analyze_user_behavior(m.from_user.id)
        time_prefs = behavior.get('preferred_time', {})
        
        if time_prefs.get('confidence', 0) > 0.7:
            preferred_hour = time_prefs.get('preferred_hour', 14)
            message += f"\n\n⏰ Ваше обычное время: {preferred_hour}:00"
        
        context = {
            "recommended_services": recommended_services,
            "preferred_time": time_prefs
        }
        await state.update_data(context=context)
        await state.set_state(SmartStates.smart_booking_service)
        
        await m.answer(
            message,
            reply_markup=smart_booking_flow_kb("service_selection", context)
        )

    # ═══════════════════════════════════════════════════════════════════
    # 📊 УМНАЯ АНАЛИТИКА И ДОСТИЖЕНИЯ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["📈 Аналитика", "📈 Статистика", "🏆 Достижения"]))
    async def smart_user_stats(m: types.Message):
        """📊 Статистика с умной аналитикой"""
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        profile = get_user_profile(m.from_user.id)
        
        # Проверяем новые достижения
        new_achievements = await achievement_system.check_achievements(m.from_user.id)
        
        # Получаем аналитику поведения
        behavior = await smart_analytics.analyze_user_behavior(m.from_user.id)
        
        message = AnalyticsTexts.user_stats(
            status=profile['loyalty_level'],
            balance=profile['balance'],
            visits=profile['visits'],
            progress=profile['loyalty_progress']
        )
        
        # Добавляем insights от умной аналитики
        engagement = behavior.get('engagement_level', 0)
        if engagement > 0.8:
            message += f"\n\n🔥 Уровень активности: Высокий ({engagement:.0%})"
        elif engagement > 0.5:
            message += f"\n\n📈 Уровень активности: Средний ({engagement:.0%})"
        
        # Показываем новые достижения
        if new_achievements:
            message += "\n\n🎉 Новые достижения:\n"
            for achievement in new_achievements:
                message += f"🏆 {achievement.title} (+{achievement.reward}₽)\n"
                # Начисляем награду
                change_balance(agent_id, achievement.reward)
        
        # Получаем все достижения пользователя
        unlocked_achievements = achievement_system._get_user_achievements(m.from_user.id)
        all_achievements = list(achievement_system.achievements.values())
        
        unlocked_count = len(unlocked_achievements)
        total_count = len(all_achievements)
        
        if unlocked_count > 0:
            message += f"\n\n🏆 Достижения: {unlocked_count}/{total_count}"
            
        await m.answer(
            message, 
            reply_markup=gamification_progress_kb(profile['loyalty_level'], profile['loyalty_progress'])
        )

    @dp.callback_query(F.data == "show_achievements")
    async def show_detailed_achievements(callback: types.CallbackQuery):
        """🏆 Подробные достижения"""
        unlocked = achievement_system._get_user_achievements(callback.from_user.id)
        all_achievements = achievement_system.achievements
        
        message = "🏆 Ваши достижения:\n\n"
        
        unlocked_rewards = 0
        for achievement_id, achievement in all_achievements.items():
            if achievement_id in unlocked:
                message += f"✅ {achievement.icon} {achievement.title}\n"
                message += f"    {achievement.description}\n"
                message += f"    💰 +{achievement.reward}₽\n\n"
                unlocked_rewards += achievement.reward
            else:
                message += f"🔒 {achievement.icon} {achievement.title}\n"
                message += f"    {achievement.description}\n"
                message += f"    💰 {achievement.reward}₽\n\n"
        
        message += f"💎 Всего заработано за достижения: {unlocked_rewards}₽"
        
        await callback.message.edit_text(message)

    # ═══════════════════════════════════════════════════════════════════
    # 🔧 УМНОЕ ТЕХОБСЛУЖИВАНИЕ
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["🔧 ТО", "🛠 ТО статус"]))
    async def smart_maintenance_status(m: types.Message):
        """🔧 Статус ТО с умными рекомендациями"""
        agent_id = get_agent_id(m.from_user.id)
        if not agent_id:
            return await m.answer(ErrorTexts.auth_required())

        status = get_all_maintenance_status(agent_id)
        summary = format_maintenance_summary(status)
        
        # Получаем рекомендации по обслуживанию
        insights = await personal_assistant.get_smart_insights(m.from_user.id)
        maintenance_insights = [i for i in insights if i.type == 'maintenance']
        
        message = (
            MaintenanceTexts.maintenance_overview() + 
            f"\n\n{summary}\n\n"
        )
        
        # Добавляем умные рекомендации
        if maintenance_insights:
            insight = maintenance_insights[0]
            message += f"💡 {insight.title}\n{insight.message}\n\n"
        
        message += "💡 Нажмите на любой пункт для подробностей"
        
        await m.answer(message)

    # ═══════════════════════════════════════════════════════════════════
    # 💬 УМНАЯ ПОДДЕРЖКА
    # ═══════════════════════════════════════════════════════════════════

    @dp.message(F.text.in_(["💬 Поддержка", "📞 Поддержка"]))
    async def smart_support(m: types.Message):
        """💬 Поддержка с учетом аналитики пользователя"""
        profile = get_user_profile(m.from_user.id)
        
        # Анализируем поведение для персонализации поддержки
        behavior = await smart_analytics.analyze_user_behavior(m.from_user.id)
        
        message = SupportTexts.support_menu(profile["level"])
        
        # Добавляем персональные советы
        engagement = behavior.get('engagement_level', 0)
        if engagement < 0.3:
            message += "\n\n💡 Видим, что вы новичок. Рекомендуем изучить раздел 'Как работают бонусы?'"
        elif engagement > 0.8:
            message += "\n\n🌟 Как активный клиент, вы можете получить дополнительные привилегии!"
        
        await m.answer(message, reply_markup=personalized_support_kb(m.from_user.id))

    # ═══════════════════════════════════════════════════════════════════
    # 🎮 ДОПОЛНИТЕЛЬНЫЕ УМНЫЕ ФУНКЦИИ
    # ═══════════════════════════════════════════════════════════════════

    @dp.callback_query(F.data == "get_referral_link")
    async def get_referral_link(callback: types.CallbackQuery):
        """👥 Получение реферальной ссылки"""
        referral_link = f"https://t.me/YourBotName?start=ref_{callback.from_user.id}"
        
        message = (
            "👥 Ваша персональная ссылка:\n\n"
            f"`{referral_link}`\n\n"
            "🎁 За каждого друга получите 500₽ бонусов!\n\n"
            "📱 Поделитесь ссылкой в соцсетях или отправьте друзьям"
        )
        
        await callback.message.edit_text(message, parse_mode='Markdown')

    @dp.callback_query(F.data == "show_savings_calculator")
    async def show_savings_calculator(callback: types.CallbackQuery):
        """💰 Калькулятор экономии"""
        profile = get_user_profile(callback.from_user.id)
        balance = profile['balance']
        
        scenarios = [
            {"service": "Замена масла", "cost": 3500, "discount": 30},
            {"service": "Диагностика", "cost": 2000, "discount": 40},
            {"service": "Комплексное ТО", "cost": 8000, "discount": 25},
        ]
        
        message = f"💰 Ваши {balance:,}₽ бонусов позволяют сэкономить:\n\n"
        
        for scenario in scenarios:
            max_discount = min(balance, int(scenario['cost'] * scenario['discount'] / 100))
            final_cost = scenario['cost'] - max_discount
            message += f"🔧 {scenario['service']}\n"
            message += f"   Цена: {scenario['cost']:,}₽\n"
            message += f"   Скидка: {max_discount:,}₽ ({scenario['discount']}%)\n"
            message += f"   К доплате: {final_cost:,}₽\n\n"
        
        await callback.message.edit_text(message)

    # ═══════════════════════════════════════════════════════════════════
    # ⚠️ ОБРАБОТКА ОШИБОК
    # ═══════════════════════════════════════════════════════════════════

    @dp.message()
    async def handle_unknown_message(m: types.Message):
        """🤷‍♂️ Обработка неизвестных сообщений с умными подсказками"""
        # Получаем контекст пользователя
        profile = get_user_profile(m.from_user.id) if get_agent_id(m.from_user.id) else None
        
        if profile:
            # Для зарегистрированных пользователей - персональные подсказки
            insights = await personal_assistant.get_smart_insights(m.from_user.id)
            
            message = (
                "🤔 Не совсем понял, что вы хотели\n\n"
                "💡 Воспользуйтесь кнопками меню — так проще!\n\n"
            )
            
            if insights:
                message += f"🎯 Возможно, вас интересует: {insights[0].title}?\n\n"
                
            message += "🆘 Если нужна помощь, нажмите 'Поддержка'"
        else:
            # Для незарегистрированных - стандартное сообщение
            message = (
                "🤔 Не совсем понял, что вы хотели\n\n"
                "💡 Воспользуйтесь кнопками меню — так проще!\n\n"
                "🆘 Если нужна помощь, нажмите 'Поддержка'"
            )
        
        await m.answer(message)

# Экспорт функции регистрации
__all__ = ['register_smart_handlers']
