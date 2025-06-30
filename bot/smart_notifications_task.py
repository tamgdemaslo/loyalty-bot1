"""
🤖 Фоновая задача для умных уведомлений
Автоматическая отправка персональных уведомлений пользователям
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from aiogram import Bot
from bot.db import conn, get_agent_id
from bot.ux_keyboards import get_user_profile
from bot.smart_features import SmartNotificationSystem, PersonalAssistant, AchievementSystem

log = logging.getLogger(__name__)

class SmartNotificationScheduler:
    """Планировщик умных уведомлений"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.notification_system = SmartNotificationSystem(bot)
        self.personal_assistant = PersonalAssistant()
        self.achievement_system = AchievementSystem()
        self.last_check = datetime.now()
    
    async def run_notification_loop(self):
        """Основной цикл отправки уведомлений"""
        log.info("🤖 Запущена система умных уведомлений")
        
        while True:
            try:
                await self._process_notifications()
                
                # Проверяем каждые 30 минут
                await asyncio.sleep(30 * 60)
                
            except Exception as e:
                log.error(f"Ошибка в системе уведомлений: {e}")
                await asyncio.sleep(60)  # Короткая пауза при ошибке
    
    async def _process_notifications(self):
        """Обработка всех типов уведомлений"""
        log.info("🔄 Проверка уведомлений...")
        
        # Получаем всех активных пользователей
        active_users = self._get_active_users()
        
        for user_id in active_users:
            try:
                await self._process_user_notifications(user_id)
            except Exception as e:
                log.error(f"Ошибка обработки уведомлений для пользователя {user_id}: {e}")
    
    def _get_active_users(self) -> List[int]:
        """Получает список активных пользователей"""
        try:
            # Получаем пользователей из существующей таблицы
            result = conn.execute("""
                SELECT DISTINCT tg_id 
                FROM telegram_mapping 
                LIMIT 50
            """).fetchall()
            
            return [row[0] for row in result if row[0]]
            
        except Exception as e:
            log.error(f"Ошибка получения активных пользователей: {e}")
            # Возвращаем пустой список если база недоступна
            return []
    
    async def _process_user_notifications(self, user_id: int):
        """Обработка уведомлений для конкретного пользователя"""
        agent_id = get_agent_id(user_id)
        if not agent_id:
            return
        
        profile = get_user_profile(user_id)
        
        # 1. Проверяем новые достижения
        await self._check_achievements(user_id)
        
        # 2. Проверяем бонусы с истекающим сроком
        await self._check_bonus_expiry(user_id, profile)
        
        # 3. Проверяем рекомендации по обслуживанию
        await self._check_maintenance_reminders(user_id, agent_id)
        
        # 4. Отправляем мотивационные уведомления
        await self._send_motivational_notifications(user_id, profile)
    
    async def _check_achievements(self, user_id: int):
        """Проверка и уведомление о новых достижениях"""
        try:
            new_achievements = await self.achievement_system.check_achievements(user_id)
            
            for achievement in new_achievements:
                await self.notification_system.send_smart_notification(
                    user_id=user_id,
                    notification_type='achievement_unlocked',
                    achievement=achievement
                )
                
                log.info(f"🏆 Отправлено уведомление о достижении '{achievement.title}' пользователю {user_id}")
                
        except Exception as e:
            log.error(f"Ошибка проверки достижений для {user_id}: {e}")
    
    async def _check_bonus_expiry(self, user_id: int, profile: dict):
        """Проверка истечения срока бонусов"""
        try:
            balance = profile.get('balance', 0)
            
            if balance > 500:
                # Имитируем проверку срока действия бонусов
                # В реальной системе здесь была бы проверка базы данных
                
                # Уведомляем за 7 дней до истечения
                await self.notification_system.send_smart_notification(
                    user_id=user_id,
                    notification_type='bonus_expiry',
                    days_left=7,
                    amount=balance
                )
                
        except Exception as e:
            log.error(f"Ошибка проверки срока бонусов для {user_id}: {e}")
    
    async def _check_maintenance_reminders(self, user_id: int, agent_id: str):
        """Проверка напоминаний о техобслуживании"""
        try:
            # Получаем инсайты от персонального помощника
            insights = await self.personal_assistant.get_smart_insights(user_id)
            maintenance_insights = [i for i in insights if i.type == 'maintenance']
            
            if maintenance_insights:
                insight = maintenance_insights[0]
                
                await self.notification_system.send_smart_notification(
                    user_id=user_id,
                    notification_type='maintenance_due',
                    service='ТО',
                    km_left=5000  # Примерное значение
                )
                
        except Exception as e:
            log.error(f"Ошибка проверки напоминаний ТО для {user_id}: {e}")
    
    async def _send_motivational_notifications(self, user_id: int, profile: dict):
        """Отправка мотивационных уведомлений"""
        try:
            # Проверяем, нужно ли отправить мотивационное сообщение
            last_visit = self._get_last_visit_date(user_id)
            
            if last_visit and (datetime.now() - last_visit).days > 30:
                # Пользователь давно не посещал сервис
                
                # Создаем специальное предложение
                await self.notification_system.send_smart_notification(
                    user_id=user_id,
                    notification_type='special_offer',
                    offer='Диагностика со скидкой для возвращающихся клиентов',
                    discount=20
                )
                
        except Exception as e:
            log.error(f"Ошибка отправки мотивационных уведомлений для {user_id}: {e}")
    
    def _get_last_visit_date(self, user_id: int) -> datetime:
        """Получает дату последнего визита"""
        try:
            # Здесь была бы реальная логика получения даты из базы
            # Пока возвращаем примерную дату
            return datetime.now() - timedelta(days=20)
            
        except Exception as e:
            log.error(f"Ошибка получения даты последнего визита для {user_id}: {e}")
            return None
    
    async def send_daily_insights(self):
        """Отправляет ежедневные инсайты активным пользователям"""
        try:
            # Отправляем только VIP клиентам
            vip_users = self._get_vip_users()
            
            for user_id in vip_users[:10]:  # Ограничиваем количество
                try:
                    insights = await self.personal_assistant.get_smart_insights(user_id)
                    
                    if insights:
                        top_insight = insights[0]
                        
                        message = (
                            f"🌅 Доброе утро!\n\n"
                            f"{top_insight.emoji} {top_insight.title}\n"
                            f"{top_insight.message}\n\n"
                            f"💪 Хорошего дня!"
                        )
                        
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=message
                        )
                        
                        log.info(f"📨 Отправлен утренний инсайт пользователю {user_id}")
                        
                except Exception as e:
                    log.error(f"Ошибка отправки утреннего инсайта {user_id}: {e}")
                    
        except Exception as e:
            log.error(f"Ошибка отправки ежедневных инсайтов: {e}")
    
    def _get_vip_users(self) -> List[int]:
        """Получает список VIP пользователей"""
        try:
            # Здесь была бы логика определения VIP пользователей
            # Пока возвращаем первые 10 активных пользователей
            return self._get_active_users()[:10]
            
        except Exception as e:
            log.error(f"Ошибка получения VIP пользователей: {e}")
            return []

async def start_smart_notifications(bot: Bot):
    """Запускает систему умных уведомлений"""
    scheduler = SmartNotificationScheduler(bot)
    
    # Запускаем основной цикл уведомлений
    notification_task = asyncio.create_task(scheduler.run_notification_loop())
    
    # Запускаем ежедневные инсайты (каждое утро в 9:00)
    async def daily_insights_loop():
        while True:
            now = datetime.now()
            # Ждем до 9:00 следующего дня
            next_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now.hour >= 9:
                next_9am += timedelta(days=1)
            
            sleep_seconds = (next_9am - now).total_seconds()
            await asyncio.sleep(sleep_seconds)
            
            await scheduler.send_daily_insights()
    
    daily_task = asyncio.create_task(daily_insights_loop())
    
    return notification_task, daily_task

# Экспорт
__all__ = ['start_smart_notifications', 'SmartNotificationScheduler']
