const express = require('express');
const path = require('path');
const cors = require('cors');
const crypto = require('crypto');
const LoyaltyAPI = require('./api_integration');

// Создаем экземпляр API
const loyaltyAPI = new LoyaltyAPI();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Telegram Bot Token для валидации
const BOT_TOKEN = process.env.BOT_TOKEN || '7914899311:AAGY4CjuMqZX3w1eS7zCM2yNMW3312xCwPE';

// Функция валидации данных из Telegram WebApp
function validateTelegramWebAppData(initData) {
    try {
        const urlParams = new URLSearchParams(initData);
        const hash = urlParams.get('hash');
        urlParams.delete('hash');
        
        const dataCheckString = Array.from(urlParams.entries())
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([key, value]) => `${key}=${value}`)
            .join('\n');
        
        const secretKey = crypto
            .createHmac('sha256', 'WebAppData')
            .update(BOT_TOKEN)
            .digest();
        
        const calculatedHash = crypto
            .createHmac('sha256', secretKey)
            .update(dataCheckString)
            .digest('hex');
        
        return calculatedHash === hash;
    } catch (error) {
        console.error('Validation error:', error);
        return false;
    }
}

// Главная страница Mini App
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API эндпоинты

// Получение данных пользователя
app.post('/api/user', async (req, res) => {
    const { initData } = req.body;
    
    // В продакшене обязательно валидировать данные
    // if (!validateTelegramWebAppData(initData)) {
    //     return res.status(401).json({ error: 'Unauthorized' });
    // }
    
    try {
        // Парсим данные пользователя
        const urlParams = new URLSearchParams(initData);
        const userParam = urlParams.get('user');
        let user = null;
        
        if (userParam) {
            try {
                user = JSON.parse(decodeURIComponent(userParam));
            } catch (error) {
                console.error('Error parsing user data:', error);
                return res.status(400).json({ error: 'Invalid user data' });
            }
        }
        
        if (!user || !user.id) {
            return res.status(400).json({ error: 'User ID not found' });
        }
        
        const loyaltyAPI = new LoyaltyAPI();
        
        // Получаем ID агента по Telegram ID
        const agentId = await loyaltyAPI.getAgentId(user.id);
        if (!agentId) {
            return res.status(404).json({ error: 'User not registered' });
        }
        
        // Получаем все данные пользователя
        const [balance, loyaltyLevel, contact, statistics] = await Promise.all([
            loyaltyAPI.getBalance(agentId),
            loyaltyAPI.getLoyaltyLevel(agentId),
            loyaltyAPI.getUserContact(user.id),
            loyaltyAPI.getClientStatistics(agentId)
        ]);
        
        // Форматируем уровни лояльности
        const levelNames = ['', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'];
        const levelName = levelNames[loyaltyLevel.level_id] || 'Bronze';
        
        const userData = {
            id: user.id,
            name: contact.fullname || user.first_name || 'Пользователь',
            phone: contact.phone || 'Не указан',
            balance: Math.round(balance / 100), // Конвертируем копейки в рубли
            level: levelName,
            levelId: loyaltyLevel.level_id,
            totalSpent: Math.round(loyaltyLevel.total_spent / 100),
            totalEarned: Math.round(loyaltyLevel.total_earned / 100),
            totalRedeemed: Math.round(loyaltyLevel.total_redeemed / 100),
            totalVisits: statistics.totalVisits,
            thisYearVisits: statistics.thisYearVisits,
            averageCheck: Math.round(statistics.averageCheck / 100),
            registeredDate: new Date().toISOString().split('T')[0]
        };
        
        res.json(userData);
    } catch (error) {
        console.error('Error getting user data:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Получение истории посещений
app.get('/api/visits/:userId', async (req, res) => {
    const { userId } = req.params;
    
    try {
        const loyaltyAPI = new LoyaltyAPI();
        
        // Получаем ID агента по Telegram ID
        const agentId = await loyaltyAPI.getAgentId(parseInt(userId));
        if (!agentId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Получаем посещения
        const visits = await loyaltyAPI.getRecentVisits(agentId, 50);
        
        // Форматируем данные для фронтенда
        const formattedVisits = visits.map(visit => ({
            id: visit.id,
            title: `Чек №${visit.name}`,
            amount: Math.round(visit.sum / 100), // Конвертируем копейки в рубли
            date: visit.moment.split('T')[0],
            services: visit.services || [],
            car: visit.car || {},
            bonusEarned: Math.round(visit.bonusEarned / 100)
        }));
        
        res.json(formattedVisits);
    } catch (error) {
        console.error('Error getting visits:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Получение транзакций
app.get('/api/transactions/:userId', async (req, res) => {
    const { userId } = req.params;
    
    try {
        const loyaltyAPI = new LoyaltyAPI();
        
        // Получаем ID агента по Telegram ID
        const agentId = await loyaltyAPI.getAgentId(parseInt(userId));
        if (!agentId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Получаем транзакции
        const transactions = await loyaltyAPI.getTransactions(agentId, 50);
        
        // Форматируем данные для фронтенда
        const formattedTransactions = transactions.map((transaction, index) => ({
            id: index + 1,
            type: transaction.transaction_type,
            description: transaction.description,
            amount: Math.round(transaction.amount / 100), // Конвертируем копейки в рубли
            date: transaction.created_at.split(' ')[0], // Берем только дату
            visitId: transaction.related_demand_id
        }));
        
        res.json(formattedTransactions);
    } catch (error) {
        console.error('Error getting transactions:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Получение данных о техническом обслуживании
app.get('/api/maintenance/:userId', async (req, res) => {
    const { userId } = req.params;
    
    try {
        const loyaltyAPI = new LoyaltyAPI();
        
        // Получаем ID агента по Telegram ID
        const agentId = await loyaltyAPI.getAgentId(parseInt(userId));
        if (!agentId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Получаем данные ТО
        const maintenanceHistory = await loyaltyAPI.getMaintenanceData(agentId);
        
        // Демо данные для базовых видов ТО
        const maintenanceWorks = {
            'oil_change': {
                title: '🛢️ Замена моторного масла',
                subtitle: 'Каждые 10,000 км или 12 месяцев',
                interval: 10000
            },
            'air_filter': {
                title: '🌬️ Замена воздушного фильтра',
                subtitle: 'Каждые 15,000 км или 18 месяцев',
                interval: 15000
            },
            'brake_check': {
                title: '🛑 Проверка тормозной системы',
                subtitle: 'Каждые 20,000 км или 24 месяца',
                interval: 20000
            },
            'battery_check': {
                title: '🔋 Диагностика аккумулятора',
                subtitle: 'Каждые 30,000 км или 36 месяцев',
                interval: 30000
            }
        };
        
        const maintenanceData = Object.keys(maintenanceWorks).map((workId, index) => {
            const work = maintenanceWorks[workId];
            const lastRecord = maintenanceHistory.find(record => record.work_id === workId);
            
            let status = 'ok';
            const currentMileage = 45000; // Это нужно получать из данных автомобиля
            
            if (lastRecord) {
                const nextDue = lastRecord.mileage + work.interval;
                if (currentMileage >= nextDue) {
                    status = 'overdue';
                } else if (currentMileage >= nextDue - 2000) {
                    status = 'soon';
                }
            } else {
                status = 'soon'; // Если работа никогда не выполнялась
            }
            
            return {
                id: index + 1,
                title: work.title,
                subtitle: work.subtitle,
                status,
                lastPerformed: lastRecord ? lastRecord.performed_date : null,
                lastMileage: lastRecord ? lastRecord.mileage : null,
                nextDue: lastRecord ? lastRecord.mileage + work.interval : currentMileage + work.interval,
                currentMileage,
                intervalKm: work.interval,
                intervalMonths: 12
            };
        });
        
        res.json(maintenanceData);
    } catch (error) {
        console.error('Error getting maintenance data:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Списание бонусов
app.post('/api/redeem', async (req, res) => {
    const { userId, amount, description } = req.body;
    
    try {
        const loyaltyAPI = new LoyaltyAPI();
        
        // Получаем ID агента по Telegram ID
        const agentId = await loyaltyAPI.getAgentId(parseInt(userId));
        if (!agentId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Проверяем текущий баланс
        const currentBalance = await loyaltyAPI.getBalance(agentId);
        const amountInKopecks = amount * 100; // Конвертируем в копейки
        
        if (currentBalance < amountInKopecks) {
            return res.status(400).json({ 
                error: 'Insufficient balance',
                message: 'Недостаточно бонусов для списания'
            });
        }
        
        // Списываем бонусы (отрицательная сумма)
        await loyaltyAPI.addBonusTransaction(
            agentId, 
            'redemption', 
            -amountInKopecks, 
            description || `Списание ${amount} бонусов через Mini App`
        );
        
        // Обновляем баланс в таблице bonuses
        const db = loyaltyAPI.db;
        await new Promise((resolve, reject) => {
            db.run(
                "UPDATE bonuses SET balance = balance - ? WHERE agent_id = ?",
                [amountInKopecks, agentId],
                function(err) {
                    if (err) reject(err);
                    else resolve();
                }
            );
        });
        
        const newBalance = await loyaltyAPI.getBalance(agentId);
        
        res.json({
            success: true,
            message: `Успешно списано ${amount} бонусов`,
            newBalance: Math.round(newBalance / 100),
            transactionId: Date.now()
        });
    } catch (error) {
        console.error('Error redeeming bonuses:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Создание записи на обслуживание
app.post('/api/booking', (req, res) => {
    const { userId, serviceId, staffId, datetime } = req.body;
    
    // Здесь должна быть интеграция с YCLIENTS
    
    // Имитация успешной записи
    setTimeout(() => {
        res.json({
            success: true,
            message: 'Запись успешно создана',
            bookingId: Date.now(),
            datetime: datetime
        });
    }, 1500);
});

// Добавление записи о ТО
app.post('/api/maintenance', (req, res) => {
    const { userId, workId, date, mileage, notes } = req.body;
    
    // Здесь должна быть логика сохранения в базе данных
    
    res.json({
        success: true,
        message: 'Запись о ТО успешно добавлена',
        recordId: Date.now()
    });
});

// Получение услуг для записи
app.get('/api/services', (req, res) => {
    const services = [
        { id: 1, title: 'Замена масла', duration: 60, price: 3500 },
        { id: 2, title: 'Диагностика двигателя', duration: 90, price: 2500 },
        { id: 3, title: 'ТО-15000', duration: 180, price: 8500 },
        { id: 4, title: 'Развал-схождение', duration: 120, price: 3200 },
        { id: 5, title: 'Замена тормозных колодок', duration: 150, price: 6500 }
    ];
    
    res.json(services);
});

// Получение мастеров
app.get('/api/staff/:serviceId', (req, res) => {
    const staff = [
        { id: 1, name: 'Иван Петрович', specialization: 'Двигатель' },
        { id: 2, name: 'Сергей Николаевич', specialization: 'Ходовая часть' },
        { id: 3, name: 'Алексей Михайлович', specialization: 'Электрика' }
    ];
    
    res.json(staff);
});

// Получение доступных слотов времени
app.get('/api/slots/:staffId/:date', (req, res) => {
    const { staffId, date } = req.params;
    
    // Демо данные доступных слотов
    const slots = [
        { time: '09:00', datetime: `${date}T09:00:00` },
        { time: '10:30', datetime: `${date}T10:30:00` },
        { time: '14:00', datetime: `${date}T14:00:00` },
        { time: '15:30', datetime: `${date}T15:30:00` },
        { time: '17:00', datetime: `${date}T17:00:00` }
    ];
    
    res.json(slots);
});

// Обработка ошибок
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Внутренняя ошибка сервера' });
});

// 404 обработчик
app.use((req, res) => {
    res.status(404).json({ error: 'Эндпоинт не найден' });
});

app.listen(PORT, () => {
    console.log(`🚀 Сервер Telegram Mini App запущен на порту ${PORT}`);
    console.log(`📱 Откройте приложение: http://localhost:${PORT}`);
    console.log(`🔗 Для Telegram WebApp используйте: https://your-domain.com`);
});
