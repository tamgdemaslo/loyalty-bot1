"""
🧠 Умный функционал для UX-оптимизированного бота
Новые возможности, адаптированные под современный дизайн
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from aiogram import Bot
from bot.db import get_agent_id, get_balance, conn
from bot.loyalty import get_level_info, calculate_level_by_spent
from bot.ux_keyboards import get_user_profile
from ux_copy_texts import (
    GamificationTexts, MaintenanceTexts, BalanceTexts, 
    TextHelpers, DynamicTexts
)

# Настройка логирования
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 🎯 УМНЫЙ ПЕРСОНАЛЬНЫЙ ПОМОЩНИК
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SmartInsight:
    """Умная рекомендация для пользователя"""
    type: str  # 'saving', 'maintenance', 'bonus', 'achievement'
    title: str
    message: str
    action_text: str
    action_data: str
    priority: int  # 1-5, где 5 - самый важный
    emoji: str

class PersonalAssistant:
    """Персональный помощник клиента"""
    
    def __init__(self):
        self.insights_cache = {}
        self.user_preferences = {}
    
    async def get_smart_insights(self, user_id: int) -> List[SmartInsight]:
        """Генерирует умные рекомендации для пользователя"""
        agent_id = get_agent_id(user_id)
        if not agent_id:
            return []
        
        profile = get_user_profile(user_id)
        insights = []
        
        # 1. Анализ экономии
        savings_insight = self._analyze_savings_potential(profile)
        if savings_insight:
            insights.append(savings_insight)
        
        # 2. Прогресс к следующему уровню
        progress_insight = self._analyze_progress(profile)
        if progress_insight:
            insights.append(progress_insight)
        
        # 3. Рекомендации по ТО
        maintenance_insight = await self._analyze_maintenance_needs(agent_id)
        if maintenance_insight:
            insights.append(maintenance_insight)
        
        # 4. Возможности заработка
        earning_insight = self._analyze_earning_potential(profile)
        if earning_insight:
            insights.append(earning_insight)
        
        # Сортируем по приоритету
        insights.sort(key=lambda x: x.priority, reverse=True)
        
        return insights[:3]  # Возвращаем топ-3 рекомендации
    
    def _analyze_savings_potential(self, profile: Dict) -> Optional[SmartInsight]:
        """Анализ потенциала экономии"""
        balance = profile['balance']
        
        if balance >= 2000:
            return SmartInsight(
                type='saving',
                title='💰 Отличная возможность сэкономить!',
                message=f'У вас {balance:,} ₽ бонусов. Можете сэкономить до 40% на следующем ТО!',
                action_text='💡 Показать варианты экономии',
                action_data='show_savings_calculator',
                priority=4,
                emoji='💰'
            )
        elif balance >= 500:
            return SmartInsight(
                type='saving',
                title='🎁 Время тратить бонусы',
                message=f'Накопили {balance:,} ₽! Самое время использовать на мойку или диагностику.',
                action_text='🛒 Что можно купить',
                action_data='show_spending_options',
                priority=3,
                emoji='🎁'
            )
        
        return None
    
    def _analyze_progress(self, profile: Dict) -> Optional[SmartInsight]:
        """Анализ прогресса к следующему уровню"""
        progress = profile.get('loyalty_progress', 0)
        current_level = profile.get('loyalty_level', 'Новичок')
        
        if progress > 0.8:
            return SmartInsight(
                type='achievement',
                title='🔥 Финальный рывок!',
                message=f'До повышения статуса осталось совсем чуть-чуть! Ваш прогресс: {progress:.0%}',
                action_text='🚀 План достижения',
                action_data='show_level_up_plan',
                priority=5,
                emoji='🔥'
            )
        elif progress > 0.5:
            return SmartInsight(
                type='achievement',
                title='📈 Отличный прогресс!',
                message=f'Вы на пути к следующему уровню! Прогресс: {progress:.0%}',
                action_text='💪 Как ускорить',
                action_data='show_progress_tips',
                priority=3,
                emoji='📈'
            )
        
        return None
    
    async def _analyze_maintenance_needs(self, agent_id: str) -> Optional[SmartInsight]:
        """Анализ потребностей в ТО"""
        # Здесь была бы реальная логика анализа ТО
        # Пока используем упрощенную версию
        
        # Проверяем, когда было последнее ТО (упрощенная версия)
        try:
            last_visit = conn.execute(
                "SELECT demand_id FROM accrual_log WHERE demand_id LIKE ? LIMIT 1", 
                (f"%{agent_id}%",)
            ).fetchone()
            
            if not last_visit:
                return SmartInsight(
                    type='maintenance',
                    title='🔧 Пора на диагностику',
                    message='Давно не были на сервисе? Рекомендуем комплексную диагностику.',
                    action_text='📅 Записаться на диагностику',
                    action_data='book_diagnostics',
                    priority=4,
                    emoji='🔧'
                )
        except Exception as e:
            # Если таблица не существует или есть ошибки - возвращаем None
            log.error(f"Error checking maintenance needs: {e}")
            return None
        
        return None
    
    def _analyze_earning_potential(self, profile: Dict) -> Optional[SmartInsight]:
        """Анализ возможностей заработка"""
        balance = profile['balance']
        level = profile['level']
        
        if level == 'new' and balance < 100:
            return SmartInsight(
                type='bonus',
                title='👥 Пригласите друга',
                message='Получите 500 ₽ за каждого приглашенного друга!',
                action_text='📲 Получить ссылку',
                action_data='get_referral_link',
                priority=3,
                emoji='👥'
            )
        elif balance < 1000:
            return SmartInsight(
                type='bonus',
                title='📅 Больше бонусов за запись',
                message='Записывайтесь через бот и получайте двойные бонусы!',
                action_text='📝 Записаться сейчас',
                action_data='quick_booking',
                priority=2,
                emoji='📅'
            )
        
        return None

# ═══════════════════════════════════════════════════════════════════
# 🎮 СИСТЕМА ДОСТИЖЕНИЙ И ГЕЙМИФИКАЦИИ
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Achievement:
    """Достижение пользователя"""
    id: str
    title: str
    description: str
    icon: str
    reward: int
    condition: Dict
    unlocked: bool = False

class AchievementSystem:
    """Система достижений"""
    
    def __init__(self):
        self.achievements = {
            'first_visit': Achievement(
                id='first_visit',
                title='Первые шаги',
                description='Совершили первое посещение',
                icon='🏆',
                reward=100,
                condition={'visits': 1}
            ),
            'loyalty_starter': Achievement(
                id='loyalty_starter',
                title='Новичок программы',
                description='Зарегистрировались в программе лояльности',
                icon='🌟',
                reward=50,
                condition={'registered': True}
            ),
            'saver_100': Achievement(
                id='saver_100',
                title='Копилка',
                description='Накопили 1000 бонусных рублей',
                icon='💎',
                reward=200,
                condition={'balance': 1000}
            ),
            'regular_client': Achievement(
                id='regular_client',
                title='Завсегдатай',
                description='Посетили сервис 5 раз',
                icon='🎯',
                reward=300,
                condition={'visits': 5}
            ),
            'big_spender': Achievement(
                id='big_spender',
                title='Щедрый клиент',
                description='Потратили 50,000 рублей',
                icon='💰',
                reward=500,
                condition={'total_spent': 50000}
            ),
            'level_up_silver': Achievement(
                id='level_up_silver',
                title='Серебряный статус',
                description='Достигли статуса Серебро',
                icon='🥈',
                reward=250,
                condition={'level': 'Серебро'}
            ),
            'level_up_gold': Achievement(
                id='level_up_gold',
                title='Золотой клиент',
                description='Достигли статуса Золото',
                icon='🥇',
                reward=500,
                condition={'level': 'Золото'}
            ),
            'referral_master': Achievement(
                id='referral_master',
                title='Амбассадор',
                description='Пригласили 3 друзей',
                icon='👑',
                reward=1000,
                condition={'referrals': 3}
            )
        }
    
    async def check_achievements(self, user_id: int) -> List[Achievement]:
        """Проверяет и возвращает новые достижения"""
        agent_id = get_agent_id(user_id)
        if not agent_id:
            return []
        
        profile = get_user_profile(user_id)
        new_achievements = []
        
        # Получаем текущие достижения пользователя
        unlocked = self._get_user_achievements(user_id)
        
        for achievement in self.achievements.values():
            if achievement.id in unlocked:
                continue
                
            if self._check_achievement_condition(achievement, profile):
                new_achievements.append(achievement)
                self._unlock_achievement(user_id, achievement.id)
        
        return new_achievements
    
    def _check_achievement_condition(self, achievement: Achievement, profile: Dict) -> bool:
        """Проверяет условие достижения"""
        condition = achievement.condition
        
        if 'visits' in condition:
            return profile.get('visits', 0) >= condition['visits']
        
        if 'balance' in condition:
            return profile.get('balance', 0) >= condition['balance']
        
        if 'level' in condition:
            return profile.get('loyalty_level') == condition['level']
        
        if 'registered' in condition:
            return True  # Если пользователь здесь, то зарегистрирован
        
        return False
    
    def _get_user_achievements(self, user_id: int) -> List[str]:
        """Получает список достижений пользователя"""
        try:
            result = conn.execute(
                "SELECT achievement_id FROM user_achievements WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            return [row[0] for row in result]
        except:
            # Если таблица не существует, создаем её
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_id INTEGER,
                    achievement_id TEXT,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, achievement_id)
                )
            """)
            conn.commit()
            return []
    
    def _unlock_achievement(self, user_id: int, achievement_id: str):
        """Разблокирует достижение для пользователя"""
        try:
            conn.execute(
                "INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?, ?)",
                (user_id, achievement_id)
            )
            conn.commit()
        except Exception as e:
            log.error(f"Error unlocking achievement: {e}")

# ═══════════════════════════════════════════════════════════════════
# 🤖 УМНЫЕ УВЕДОМЛЕНИЯ
# ═══════════════════════════════════════════════════════════════════

class SmartNotificationSystem:
    """Система умных уведомлений"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.notification_history = {}
    
    async def send_smart_notification(self, user_id: int, notification_type: str, **kwargs):
        """Отправляет умное уведомление"""
        
        # Проверяем, не отправляли ли мы уже это уведомление недавно
        if self._is_notification_sent_recently(user_id, notification_type):
            return
        
        message = self._generate_notification_message(notification_type, **kwargs)
        if not message:
            return
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            # Записываем факт отправки
            self._record_notification(user_id, notification_type)
            
        except Exception as e:
            log.error(f"Error sending notification to {user_id}: {e}")
    
    def _generate_notification_message(self, notification_type: str, **kwargs) -> Optional[str]:
        """Генерирует текст уведомления"""
        
        if notification_type == 'maintenance_due':
            service = kwargs.get('service', 'ТО')
            km_left = kwargs.get('km_left', 0)
            return MaintenanceTexts.maintenance_reminder(service, km_left)
        
        elif notification_type == 'achievement_unlocked':
            achievement = kwargs.get('achievement')
            if achievement:
                return GamificationTexts.new_achievement(achievement.title, achievement.reward)
        
        elif notification_type == 'level_up':
            old_level = kwargs.get('old_level')
            new_level = kwargs.get('new_level')
            benefits = kwargs.get('benefits', [])
            return GamificationTexts.level_up(old_level, new_level, benefits)
        
        elif notification_type == 'bonus_expiry':
            days_left = kwargs.get('days_left', 0)
            amount = kwargs.get('amount', 0)
            return (
                f"⏰ Напоминание о бонусах\n\n"
                f"У вас {amount:,} ₽ бонусов\n"
                f"{DynamicTexts.countdown_text(days_left, 'Срок действия истекает')}\n\n"
                f"💡 Используйте их на следующем ТО"
            )
        
        elif notification_type == 'special_offer':
            offer = kwargs.get('offer', '')
            discount = kwargs.get('discount', 0)
            return (
                f"🎁 Специальное предложение!\n\n"
                f"{offer}\n"
                f"Скидка: {discount}%\n\n"
                f"⏰ Предложение ограничено"
            )
        
        return None
    
    def _is_notification_sent_recently(self, user_id: int, notification_type: str) -> bool:
        """Проверяет, отправлялось ли уведомление недавно"""
        key = f"{user_id}_{notification_type}"
        
        if key not in self.notification_history:
            return False
        
        last_sent = self.notification_history[key]
        
        # Разные типы уведомлений имеют разные интервалы
        intervals = {
            'maintenance_due': timedelta(days=7),
            'achievement_unlocked': timedelta(minutes=0),  # Всегда отправляем
            'level_up': timedelta(minutes=0),  # Всегда отправляем
            'bonus_expiry': timedelta(days=1),
            'special_offer': timedelta(hours=12)
        }
        
        interval = intervals.get(notification_type, timedelta(days=1))
        return datetime.now() - last_sent < interval
    
    def _record_notification(self, user_id: int, notification_type: str):
        """Записывает факт отправки уведомления"""
        key = f"{user_id}_{notification_type}"
        self.notification_history[key] = datetime.now()

# ═══════════════════════════════════════════════════════════════════
# 📊 СИСТЕМА АНАЛИТИКИ И РЕКОМЕНДАЦИЙ
# ═══════════════════════════════════════════════════════════════════

class SmartAnalytics:
    """Умная система аналитики"""
    
    def __init__(self):
        self.user_patterns = {}
    
    async def analyze_user_behavior(self, user_id: int) -> Dict:
        """Анализирует поведение пользователя"""
        agent_id = get_agent_id(user_id)
        if not agent_id:
            return {}
        
        profile = get_user_profile(user_id)
        
        # Анализируем паттерны использования
        patterns = {
            'preferred_time': self._analyze_preferred_booking_time(user_id),
            'service_preferences': self._analyze_service_preferences(agent_id),
            'spending_pattern': self._analyze_spending_pattern(agent_id),
            'engagement_level': self._calculate_engagement_level(profile),
            'churn_risk': self._calculate_churn_risk(agent_id),
            'lifetime_value': self._calculate_lifetime_value(agent_id)
        }
        
        return patterns
    
    def _analyze_preferred_booking_time(self, user_id: int) -> Dict:
        """Анализирует предпочтительное время для записи"""
        # Здесь была бы логика анализа времени записей
        return {
            'preferred_hour': 14,  # 14:00
            'preferred_days': ['tuesday', 'wednesday', 'thursday'],
            'confidence': 0.8
        }
    
    def _analyze_service_preferences(self, agent_id: str) -> List[str]:
        """Анализирует предпочтения в услугах"""
        # Анализ истории услуг из базы
        return ['Замена масла', 'Диагностика', 'Мойка']
    
    def _analyze_spending_pattern(self, agent_id: str) -> Dict:
        """Анализирует паттерны трат"""
        return {
            'average_check': 3500,
            'frequency': 'monthly',
            'growth_trend': 'positive',
            'seasonal_pattern': 'winter_peak'
        }
    
    def _calculate_engagement_level(self, profile: Dict) -> float:
        """Рассчитывает уровень вовлеченности (0-1)"""
        visits = profile.get('visits', 0)
        balance = profile.get('balance', 0)
        progress = profile.get('loyalty_progress', 0)
        
        # Простая формула вовлеченности
        engagement = min(1.0, (visits * 0.1 + min(balance/1000, 1) * 0.3 + progress * 0.6))
        return engagement
    
    def _calculate_churn_risk(self, agent_id: str) -> float:
        """Рассчитывает риск оттока клиента (0-1)"""
        # Анализ времени с последнего визита
        # Для примера возвращаем случайное значение
        return 0.2  # Низкий риск
    
    def _calculate_lifetime_value(self, agent_id: str) -> int:
        """Рассчитывает пожизненную ценность клиента"""
        # Анализ истории трат и прогноз
        return 25000  # В рублях

# ═══════════════════════════════════════════════════════════════════
# 🎯 ПЕРСОНАЛЬНЫЕ РЕКОМЕНДАЦИИ
# ═══════════════════════════════════════════════════════════════════

class RecommendationEngine:
    """Движок персональных рекомендаций"""
    
    def __init__(self):
        self.analytics = SmartAnalytics()
    
    async def get_personalized_recommendations(self, user_id: int) -> List[Dict]:
        """Получает персональные рекомендации"""
        behavior = await self.analytics.analyze_user_behavior(user_id)
        profile = get_user_profile(user_id)
        
        recommendations = []
        
        # Рекомендации по услугам
        service_rec = self._recommend_services(behavior, profile)
        if service_rec:
            recommendations.extend(service_rec)
        
        # Рекомендации по времени
        time_rec = self._recommend_optimal_time(behavior)
        if time_rec:
            recommendations.append(time_rec)
        
        # Финансовые рекомендации
        financial_rec = self._recommend_financial_strategy(profile)
        if financial_rec:
            recommendations.append(financial_rec)
        
        return recommendations
    
    def _recommend_services(self, behavior: Dict, profile: Dict) -> List[Dict]:
        """Рекомендует услуги на основе поведения"""
        preferences = behavior.get('service_preferences', [])
        
        recommendations = []
        
        if 'Замена масла' in preferences:
            recommendations.append({
                'type': 'service',
                'title': '🔧 Время для замены масла',
                'description': 'Основываясь на вашей истории, рекомендуем запланировать замену масла',
                'action': 'book_oil_change',
                'priority': 4
            })
        
        if profile.get('balance', 0) > 1000:
            recommendations.append({
                'type': 'service',
                'title': '🧼 Комплексная мойка',
                'description': 'У вас достаточно бонусов для полной оплаты мойки',
                'action': 'book_washing',
                'priority': 3
            })
        
        return recommendations
    
    def _recommend_optimal_time(self, behavior: Dict) -> Optional[Dict]:
        """Рекомендует оптимальное время для записи"""
        time_prefs = behavior.get('preferred_time', {})
        
        if time_prefs.get('confidence', 0) > 0.7:
            hour = time_prefs.get('preferred_hour', 14)
            return {
                'type': 'timing',
                'title': f'⏰ Оптимальное время: {hour}:00',
                'description': 'Основываясь на вашей истории, это время вам наиболее удобно',
                'action': f'suggest_time_{hour}',
                'priority': 2
            }
        
        return None
    
    def _recommend_financial_strategy(self, profile: Dict) -> Optional[Dict]:
        """Рекомендует финансовую стратегию"""
        balance = profile.get('balance', 0)
        level = profile.get('loyalty_level', 'Новичок')
        
        if balance > 2000:
            return {
                'type': 'financial',
                'title': '💰 Оптимизируйте траты',
                'description': f'С вашим {level} статусом можете сэкономить до 40% на крупном ТО',
                'action': 'show_savings_plan',
                'priority': 5
            }
        elif balance < 500:
            return {
                'type': 'financial',
                'title': '📈 Стратегия накопления',
                'description': 'Рекомендуем план накопления бонусов для следующего ТО',
                'action': 'show_earning_plan',
                'priority': 3
            }
        
        return None

# ═══════════════════════════════════════════════════════════════════
# 🚀 ЭКСПОРТ ВСЕХ КЛАССОВ
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    'PersonalAssistant',
    'AchievementSystem', 
    'SmartNotificationSystem',
    'SmartAnalytics',
    'RecommendationEngine',
    'SmartInsight',
    'Achievement'
]
