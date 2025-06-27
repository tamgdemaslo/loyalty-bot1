"""
🧠 Упрощённые умные функции для бота
Минимум геймификации, максимум пользы
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from bot.db import get_agent_id, get_balance, conn
from bot.ux_keyboards import get_user_profile
from ux_copy_texts_minimal import MaintenanceTexts, GamificationTexts, DynamicTexts

log = logging.getLogger(__name__)

@dataclass
class SmartInsight:
    """Простая рекомендация для пользователя"""
    type: str  # 'saving', 'maintenance', 'bonus'
    title: str
    message: str
    action_text: str
    action_data: str

class PersonalAssistant:
    """Упрощённый персональный помощник"""
    
    def __init__(self):
        self.insights_cache = {}
    
    async def get_smart_insights(self, user_id: int) -> List[SmartInsight]:
        """Генерирует простые рекомендации"""
        agent_id = get_agent_id(user_id)
        if not agent_id:
            return []
        
        profile = get_user_profile(user_id)
        insights = []
        
        # Анализ баланса
        balance_insight = self._analyze_balance(profile)
        if balance_insight:
            insights.append(balance_insight)
        
        # Рекомендации по обслуживанию
        maintenance_insight = self._analyze_maintenance(agent_id)
        if maintenance_insight:
            insights.append(maintenance_insight)
        
        return insights[:2]  # Максимум 2 рекомендации
    
    def _analyze_balance(self, profile: Dict) -> Optional[SmartInsight]:
        """Анализ баланса"""
        balance = profile['balance']
        
        if balance >= 1000:
            return SmartInsight(
                type='saving',
                title='Можете сэкономить на ТО',
                message=f'У вас {balance:,} ₽ бонусов. Используйте их при следующем обслуживании.',
                action_text='Посмотреть варианты',
                action_data='show_savings_calculator'
            )
        elif balance >= 300:
            return SmartInsight(
                type='saving',
                title='Накоплена хорошая сумма',
                message=f'{balance:,} ₽ хватит на мойку или мелкий ремонт.',
                action_text='Что можно купить',
                action_data='show_spending_options'
            )
        
        return None
    
    def _analyze_maintenance(self, agent_id: str) -> Optional[SmartInsight]:
        """Проверка потребности в обслуживании"""
        try:
            # Простая проверка наличия записей
            last_visit = conn.execute(
                "SELECT demand_id FROM accrual_log WHERE demand_id LIKE ? LIMIT 1", 
                (f"%{agent_id}%",)
            ).fetchone()
            
            if not last_visit:
                return SmartInsight(
                    type='maintenance',
                    title='Рекомендуем диагностику',
                    message='Давно не проверяли автомобиль? Диагностика поможет выявить проблемы.',
                    action_text='Записаться',
                    action_data='book_diagnostics'
                )
        except Exception as e:
            log.error(f"Error checking maintenance: {e}")
        
        return None

class SimpleAchievementSystem:
    """Упрощённая система достижений"""
    
    def __init__(self):
        self.achievements = {
            'first_visit': {
                'title': 'Первое посещение',
                'reward': 100,
                'condition': {'visits': 1}
            },
            'regular_client': {
                'title': 'Постоянный клиент',
                'reward': 200,
                'condition': {'visits': 5}
            },
            'good_saver': {
                'title': 'Накопитель',
                'reward': 150,
                'condition': {'balance': 1000}
            }
        }
    
    async def check_achievements(self, user_id: int) -> List[Dict]:
        """Проверка новых достижений (упрощённая)"""
        agent_id = get_agent_id(user_id)
        if not agent_id:
            return []
        
        profile = get_user_profile(user_id)
        unlocked = self._get_user_achievements(user_id)
        new_achievements = []
        
        for achievement_id, achievement in self.achievements.items():
            if achievement_id in unlocked:
                continue
                
            if self._check_condition(achievement['condition'], profile):
                new_achievements.append(achievement)
                self._unlock_achievement(user_id, achievement_id)
        
        return new_achievements
    
    def _check_condition(self, condition: Dict, profile: Dict) -> bool:
        """Проверка условия достижения"""
        if 'visits' in condition:
            return profile.get('visits', 0) >= condition['visits']
        if 'balance' in condition:
            return profile.get('balance', 0) >= condition['balance']
        return False
    
    def _get_user_achievements(self, user_id: int) -> List[str]:
        """Получение достижений пользователя"""
        try:
            result = conn.execute(
                "SELECT achievement_id FROM user_achievements WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            return [row[0] for row in result]
        except:
            # Создаём таблицу если её нет
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
        """Разблокировка достижения"""
        try:
            conn.execute(
                "INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?, ?)",
                (user_id, achievement_id)
            )
            conn.commit()
        except Exception as e:
            log.error(f"Error unlocking achievement: {e}")

class SimpleRecommendationEngine:
    """Упрощённый движок рекомендаций"""
    
    async def get_recommendations(self, user_id: int) -> List[Dict]:
        """Получение простых рекомендаций"""
        profile = get_user_profile(user_id)
        recommendations = []
        
        # Рекомендации по услугам
        balance = profile.get('balance', 0)
        level = profile.get('level', 'new')
        
        if balance > 500:
            recommendations.append({
                'type': 'service',
                'title': 'Комплексная мойка',
                'description': 'У вас достаточно бонусов для оплаты мойки'
            })
        
        if level == 'new':
            recommendations.append({
                'type': 'service', 
                'title': 'Диагностика',
                'description': 'Рекомендуем начать с комплексной диагностики'
            })
        
        return recommendations

# Экспорт классов
__all__ = [
    'PersonalAssistant',
    'SimpleAchievementSystem', 
    'SimpleRecommendationEngine',
    'SmartInsight'
]
