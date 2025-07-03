/**
 * Модуль управления историей посещений и транзакциями
 * Обеспечивает функциональность для отображения и работы с историей визитов
 */

class VisitManager {
    constructor() {
        this.visits = [];
        this.transactions = [];
        this.maintenanceRecords = [];
        this.userCars = [];
        this.userId = null;
    }

    /**
     * Инициализация менеджера с ID пользователя
     * @param {number} userId - ID пользователя в Telegram
     */
    init(userId) {
        this.userId = userId;
        
        // Загружаем данные
        if (userId) {
            this.loadVisits();
            this.loadTransactions();
            this.loadMaintenance();
            this.loadUserCars();
        }
    }

    /**
     * Загрузка истории посещений с сервера
     * @returns {Promise<Array>} Массив посещений
     */
    async loadVisits() {
        try {
            if (!this.userId) throw new Error('ID пользователя не определен');
            
            const response = await fetch(`/api/visits/${this.userId}`);
            if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
            
            this.visits = await response.json();
            return this.visits;
        } catch (error) {
            console.error('Ошибка загрузки посещений:', error);
            // Возвращаем демо-данные в случае ошибки
            this.visits = this.getDemoVisits();
            return this.visits;
        }
    }

    /**
     * Загрузка истории транзакций с сервера
     * @returns {Promise<Array>} Массив транзакций
     */
    async loadTransactions() {
        try {
            if (!this.userId) throw new Error('ID пользователя не определен');
            
            const response = await fetch(`/api/transactions/${this.userId}`);
            if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
            
            this.transactions = await response.json();
            return this.transactions;
        } catch (error) {
            console.error('Ошибка загрузки транзакций:', error);
            // Возвращаем демо-данные в случае ошибки
            this.transactions = this.getDemoTransactions();
            return this.transactions;
        }
    }

    /**
     * Загрузка данных о техническом обслуживании с сервера
     * @returns {Promise<Array>} Массив записей о ТО
     */
    async loadMaintenance() {
        try {
            if (!this.userId) throw new Error('ID пользователя не определен');
            
            const response = await fetch(`/api/maintenance/${this.userId}`);
            if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
            
            this.maintenanceRecords = await response.json();
            return this.maintenanceRecords;
        } catch (error) {
            console.error('Ошибка загрузки данных ТО:', error);
            // Возвращаем демо-данные в случае ошибки
            this.maintenanceRecords = this.getDemoMaintenance();
            return this.maintenanceRecords;
        }
    }

    /**
     * Загрузка данных об автомобилях пользователя
     * @returns {Promise<Array>} Массив автомобилей
     */
    async loadUserCars() {
        try {
            if (!this.userId) throw new Error('ID пользователя не определен');
            
            const response = await fetch(`/api/cars/${this.userId}`);
            if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
            
            this.userCars = await response.json();
            return this.userCars;
        } catch (error) {
            console.error('Ошибка загрузки автомобилей:', error);
            // Возвращаем демо-данные в случае ошибки
            this.userCars = this.getDemoCars();
            return this.userCars;
        }
    }

    /**
     * Получение детальной информации о посещении
     * @param {number} visitId - ID посещения
     * @returns {Promise<Object>} Данные о посещении
     */
    async getVisitDetails(visitId) {
        try {
            const response = await fetch(`/api/visit-details/${this.userId}/${visitId}`);
            if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
            
            return await response.json();
        } catch (error) {
            console.error('Ошибка загрузки деталей посещения:', error);
            // Возвращаем найденное посещение из кэша или демо-данные
            const cachedVisit = this.visits.find(v => v.id === visitId);
            return cachedVisit || {
                id: visitId,
                title: `Чек №${visitId}`,
                amount: 12500,
                date: new Date().toISOString().split('T')[0],
                services: ['Замена масла', 'Диагностика двигателя'],
                bonusEarned: 450,
                status: 'Выполнено',
                car: this.userCars[0] || {
                    make: 'Toyota',
                    model: 'Camry',
                    year: 2020,
                    licensePlate: 'A123BC'
                }
            };
        }
    }

    /**
     * Добавление новой записи о техническом обслуживании
     * @param {Object} maintenanceData - Данные о ТО
     * @returns {Promise<Object>} Результат операции
     */
    async addMaintenanceRecord(maintenanceData) {
        try {
            const response = await fetch('/api/maintenance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userId: this.userId,
                    ...maintenanceData
                })
            });
            
            if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
            
            const result = await response.json();
            
            // Обновляем кэш данных о ТО
            this.loadMaintenance();
            
            return result;
        } catch (error) {
            console.error('Ошибка добавления записи о ТО:', error);
            return { success: false, message: error.message };
        }
    }

    /**
     * Запись на обслуживание
     * @param {Object} bookingData - Данные для записи
     * @returns {Promise<Object>} Результат операции
     */
    async createBooking(bookingData) {
        try {
            const response = await fetch('/api/booking', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userId: this.userId,
                    ...bookingData
                })
            });
            
            if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
            
            return await response.json();
        } catch (error) {
            console.error('Ошибка создания записи:', error);
            return { success: false, message: error.message };
        }
    }

    /**
     * Создание демо-данных для истории посещений
     * @returns {Array} Массив демо-посещений
     */
    getDemoVisits() {
        return [
            {
                id: 1,
                title: 'Чек №12345',
                amount: 8500,
                date: '2024-05-20',
                services: ['Замена масла', 'Диагностика'],
                bonusEarned: 320
            },
            {
                id: 2,
                title: 'Чек №12344',
                amount: 15300,
                date: '2024-05-15',
                services: ['ТО-15000', 'Замена фильтров'],
                bonusEarned: 560
            },
            {
                id: 3,
                title: 'Чек №12343',
                amount: 3200,
                date: '2024-05-10',
                services: ['Развал-схождение'],
                bonusEarned: 120
            },
            {
                id: 4,
                title: 'Чек №12342',
                amount: 6800,
                date: '2024-04-25',
                services: ['Замена тормозных колодок'],
                bonusEarned: 250
            },
            {
                id: 5,
                title: 'Чек №12341',
                amount: 4500,
                date: '2024-04-18',
                services: ['Замена ламп'],
                bonusEarned: 170
            }
        ];
    }

    /**
     * Создание демо-данных для истории транзакций
     * @returns {Array} Массив демо-транзакций
     */
    getDemoTransactions() {
        return [
            {
                id: 1,
                type: 'accrual',
                description: 'Начисление за посещение',
                amount: 320,
                date: '2024-05-20',
                visitId: 1
            },
            {
                id: 2,
                type: 'accrual',
                description: 'Начисление за посещение',
                amount: 560,
                date: '2024-05-15',
                visitId: 2
            },
            {
                id: 3,
                type: 'redemption',
                description: 'Списание бонусов',
                amount: -500,
                date: '2024-05-12',
                visitId: null
            },
            {
                id: 4,
                type: 'accrual',
                description: 'Начисление за посещение',
                amount: 120,
                date: '2024-05-10',
                visitId: 3
            },
            {
                id: 5,
                type: 'accrual',
                description: 'Начисление за посещение',
                amount: 250,
                date: '2024-04-25',
                visitId: 4
            },
            {
                id: 6,
                type: 'accrual',
                description: 'Приветственные бонусы',
                amount: 100,
                date: '2024-04-15',
                visitId: null
            }
        ];
    }

    /**
     * Создание демо-данных для технического обслуживания
     * @returns {Array} Массив демо-записей о ТО
     */
    getDemoMaintenance() {
        return [
            {
                id: 1,
                title: '🛢️ Замена моторного масла',
                subtitle: 'Каждые 10,000 км или 12 месяцев',
                status: 'soon',
                lastPerformed: '2024-03-15',
                lastMileage: 40000,
                nextDue: 50000,
                currentMileage: 48500,
                intervalKm: 10000,
                intervalMonths: 12
            },
            {
                id: 2,
                title: '🌬️ Замена воздушного фильтра',
                subtitle: 'Каждые 15,000 км или 18 месяцев',
                status: 'ok',
                lastPerformed: '2024-05-01',
                lastMileage: 45000,
                nextDue: 60000,
                currentMileage: 48500,
                intervalKm: 15000,
                intervalMonths: 18
            },
            {
                id: 3,
                title: '🛑 Проверка тормозной системы',
                subtitle: 'Каждые 20,000 км или 24 месяца',
                status: 'overdue',
                lastPerformed: '2023-10-15',
                lastMileage: 28500,
                nextDue: 48500,
                currentMileage: 48500,
                intervalKm: 20000,
                intervalMonths: 24
            },
            {
                id: 4,
                title: '🔋 Диагностика аккумулятора',
                subtitle: 'Каждые 30,000 км или 36 месяцев',
                status: 'never',
                lastPerformed: null,
                lastMileage: null,
                nextDue: null,
                currentMileage: 48500,
                intervalKm: 30000,
                intervalMonths: 36
            }
        ];
    }

    /**
     * Создание демо-данных для автомобилей пользователя
     * @returns {Array} Массив демо-автомобилей
     */
    getDemoCars() {
        return [
            {
                id: 1,
                make: 'Toyota',
                model: 'Camry',
                year: 2020,
                licensePlate: 'A123BC',
                vin: 'YV1TS59G411103920',
                color: 'Серебристый',
                mileage: 48500
            },
            {
                id: 2,
                make: 'Nissan',
                model: 'X-Trail',
                year: 2018,
                licensePlate: 'O789PQ',
                vin: 'JN1TANT31U0005118',
                color: 'Белый',
                mileage: 75300
            }
        ];
    }

    /**
     * Получение данных о посещениях для графика
     * @returns {Object} Данные для графика
     */
    getVisitsChartData() {
        // Создаем массив месяцев за последние 6 месяцев
        const months = [];
        const now = new Date();
        for (let i = 5; i >= 0; i--) {
            const month = new Date(now.getFullYear(), now.getMonth() - i, 1);
            months.push({
                name: month.toLocaleString('ru-RU', { month: 'short' }),
                year: month.getFullYear(),
                month: month.getMonth()
            });
        }
        
        // Подсчитываем сумму посещений по месяцам
        const data = months.map(month => {
            const monthVisits = this.visits.filter(visit => {
                const visitDate = new Date(visit.date);
                return visitDate.getMonth() === month.month && 
                       visitDate.getFullYear() === month.year;
            });
            
            const totalAmount = monthVisits.reduce((sum, visit) => sum + visit.amount, 0);
            
            return {
                month: month.name,
                spent: totalAmount
            };
        });
        
        return data;
    }
}

// Экспорт для использования в других модулях
window.VisitManager = VisitManager;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.visitManager = new VisitManager();
});
