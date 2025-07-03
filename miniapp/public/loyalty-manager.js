/**
 * Модуль управления системой лояльности
 * Обеспечивает функциональность работы с бонусами и статусами
 */

class LoyaltyManager {
    constructor() {
        // Базовая конфигурация уровней лояльности
        this.levels = {
            1: { name: 'Бронза', bonus: 5, discount: 30, min: 0 },
            2: { name: 'Серебро', bonus: 7, discount: 35, min: 15000 },
            3: { name: 'Золото', bonus: 10, discount: 40, min: 40000 },
            4: { name: 'Платина', bonus: 15, discount: 50, min: 100000 },
            5: { name: 'Алмаз', bonus: 20, discount: 60, min: 200000 }
        };
        
        this.userData = null;
        this.userStats = null;
    }

    /**
     * Инициализация менеджера с данными пользователя
     * @param {Object} userData - Данные пользователя
     */
    init(userData) {
        this.userData = userData;
        
        if (userData) {
            this.calculateUserStats();
        }
    }

    /**
     * Обновление данных пользователя
     * @param {Object} userData - Новые данные пользователя
     */
    updateUserData(userData) {
        this.userData = userData;
        this.calculateUserStats();
    }

    /**
     * Вычисление статистики пользователя
     */
    calculateUserStats() {
        if (!this.userData) return;
        
        const level = this.levels[this.userData.levelId] || this.levels[1];
        const nextLevelId = this.userData.levelId + 1;
        const nextLevel = this.levels[nextLevelId];
        
        let progress = 100;
        let needed = 0;
        
        if (nextLevel) {
            progress = Math.min(((this.userData.totalSpent - level.min) / (nextLevel.min - level.min)) * 100, 100);
            needed = Math.max(0, nextLevel.min - this.userData.totalSpent);
        }
        
        this.userStats = {
            level,
            nextLevel,
            progress,
            needed,
            bonus: this.userData.balance,
            totalSpent: this.userData.totalSpent,
            totalEarned: this.userData.totalEarned,
            totalRedeemed: this.userData.totalRedeemed
        };
    }

    /**
     * Расчет бонусов для суммы чека
     * @param {number} amount - Сумма чека
     * @returns {number} Количество бонусов
     */
    calculateBonuses(amount) {
        if (!this.userData || !this.userStats) return 0;
        
        const bonusPercent = this.userStats.level.bonus;
        return Math.round(amount * bonusPercent / 100);
    }

    /**
     * Расчет максимальной суммы для списания
     * @param {number} amount - Сумма чека
     * @returns {number} Максимальная сумма списания
     */
    calculateMaxRedemption(amount) {
        if (!this.userData) return 0;
        
        // Максимальное списание - до 30% от суммы чека, но не более текущего баланса
        const maxPercent = 30;
        const maxByCheck = Math.round(amount * maxPercent / 100);
        return Math.min(maxByCheck, this.userData.balance);
    }

    /**
     * Списание бонусов
     * @param {number} amount - Количество бонусов для списания
     * @param {string} description - Описание операции
     * @returns {Promise<Object>} Результат операции
     */
    async redeemBonuses(amount, description = '') {
        try {
            if (!this.userData || !this.userData.id) {
                throw new Error('Данные пользователя не определены');
            }
            
            if (!amount || amount <= 0) {
                throw new Error('Введите корректную сумму');
            }
            
            if (amount > this.userData.balance) {
                throw new Error('Недостаточно бонусов');
            }
            
            const response = await fetch('/api/redeem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userId: this.userData.id,
                    amount,
                    description: description || `Списание ${amount} бонусов через Mini App`
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Ошибка при списании бонусов');
            }
            
            const result = await response.json();
            
            // Обновляем локальные данные
            this.userData.balance = result.newBalance;
            this.userData.totalRedeemed += amount;
            this.calculateUserStats();
            
            return {
                success: true,
                message: result.message || `Успешно списано ${amount} бонусов`,
                newBalance: result.newBalance
            };
        } catch (error) {
            console.error('Ошибка списания бонусов:', error);
            return {
                success: false,
                message: error.message || 'Произошла ошибка при списании бонусов'
            };
        }
    }

    /**
     * Получение данных для графика прогресса лояльности
     * @returns {Object} Данные для графика
     */
    getLoyaltyProgressData() {
        if (!this.userData || !this.userStats) return null;
        
        const { level, nextLevel } = this.userStats;
        
        // Если нет следующего уровня (максимальный уровень)
        if (!nextLevel) {
            return {
                labels: [level.name],
                data: [100],
                colors: ['#8A2BE2']
            };
        }
        
        // Для не максимального уровня
        return {
            labels: [level.name, nextLevel.name],
            data: [this.userStats.progress, 100 - this.userStats.progress],
            colors: [this.getLevelColor(level.name), '#e0e0e0']
        };
    }

    /**
     * Получение цвета для уровня лояльности
     * @param {string} levelName - Название уровня
     * @returns {string} HEX-код цвета
     */
    getLevelColor(levelName) {
        const colors = {
            'Бронза': '#CD7F32',
            'Серебро': '#C0C0C0',
            'Золото': '#FFD700',
            'Платина': '#E5E4E2',
            'Алмаз': '#8A2BE2'
        };
        
        return colors[levelName] || '#4CAF50';
    }

    /**
     * Получение CSS-класса для уровня лояльности
     * @param {string} levelName - Название уровня
     * @returns {string} Название CSS-класса
     */
    getLevelClass(levelName) {
        const classes = {
            'Бронза': 'gradient-bronze',
            'Серебро': 'gradient-silver',
            'Золото': 'gradient-gold',
            'Платина': 'gradient-platinum',
            'Алмаз': 'gradient-diamond'
        };
        
        return classes[levelName] || '';
    }

    /**
     * Получение информации о скидке для текущего уровня
     * @returns {string} Текстовое описание скидки
     */
    getDiscountInfo() {
        if (!this.userStats || !this.userStats.level) return '';
        
        const { bonus, discount } = this.userStats.level;
        return `${bonus}% кэшбэк • до ${discount}% скидка`;
    }
}

// Экспорт для использования в других модулях
window.LoyaltyManager = LoyaltyManager;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.loyaltyManager = new LoyaltyManager();
});
