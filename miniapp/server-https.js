const express = require('express');
const https = require('https');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const crypto = require('crypto');
const LoyaltyAPI = require('./api_integration');

const app = express();
const PORT = process.env.PORT || 3000;
const HTTPS_PORT = process.env.HTTPS_PORT || 3443;

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
app.post('/api/user', (req, res) => {
    const { initData } = req.body;
    
    // В продакшене обязательно валидировать данные
    // if (!validateTelegramWebAppData(initData)) {
    //     return res.status(401).json({ error: 'Unauthorized' });
    // }
    
    // Парсим данные пользователя
    const urlParams = new URLSearchParams(initData);
    const userParam = urlParams.get('user');
    let user = null;
    
    if (userParam) {
        try {
            user = JSON.parse(decodeURIComponent(userParam));
        } catch (error) {
            console.error('Error parsing user data:', error);
        }
    }
    
    // Здесь должен быть запрос к базе данных
    // Возвращаем демо данные
    const userData = {
        id: user?.id || 12345,
        name: user?.first_name || 'Демо пользователь',
        phone: '+7 XXX XXX-XX-XX',
        balance: 2450,
        level: 'Silver',
        totalSpent: 75000,
        totalEarned: 5420,
        totalRedeemed: 2970,
        totalVisits: 12,
        registeredDate: '2023-05-15'
    };
    
    res.json(userData);
});

// Получение истории посещений
app.get('/api/visits/:userId', (req, res) => {
    const { userId } = req.params;
    
    // Демо данные
    const visits = [
        {
            id: 1,
            title: 'Чек №12345',
            amount: 8500,
            date: '2024-01-20',
            services: ['Замена масла', 'Диагностика'],
            car: {
                model: 'Toyota Camry',
                vin: 'JT2BF28K6X0123456',
                mileage: 48500
            },
            bonusEarned: 425
        },
        {
            id: 2,
            title: 'Чек №12344',
            amount: 15300,
            date: '2024-01-15',
            services: ['ТО-15000', 'Замена фильтров'],
            car: {
                model: 'Toyota Camry',
                vin: 'JT2BF28K6X0123456',
                mileage: 45000
            },
            bonusEarned: 765
        },
        {
            id: 3,
            title: 'Чек №12343',
            amount: 3200,
            date: '2024-01-10',
            services: ['Развал-схождение'],
            car: {
                model: 'Toyota Camry',
                vin: 'JT2BF28K6X0123456',
                mileage: 44800
            },
            bonusEarned: 160
        }
    ];
    
    res.json(visits);
});

// Получение транзакций
app.get('/api/transactions/:userId', (req, res) => {
    const { userId } = req.params;
    
    // Демо данные
    const transactions = [
        {
            id: 1,
            type: 'accrual',
            description: 'Начисление за визит #12345',
            amount: 425,
            date: '2024-01-20',
            visitId: 1
        },
        {
            id: 2,
            type: 'redemption',
            description: 'Списание по чеку #12344',
            amount: -320,
            date: '2024-01-18',
            visitId: 2
        },
        {
            id: 3,
            type: 'accrual',
            description: 'Начисление за визит #12344',
            amount: 765,
            date: '2024-01-15',
            visitId: 2
        },
        {
            id: 4,
            type: 'bonus',
            description: 'Приветственный бонус',
            amount: 100,
            date: '2023-05-15',
            visitId: null
        }
    ];
    
    res.json(transactions);
});

// Получение данных о техническом обслуживании
app.get('/api/maintenance/:userId', (req, res) => {
    const { userId } = req.params;
    
    // Демо данные
    const maintenanceData = [
        {
            id: 1,
            title: '🛢️ Замена моторного масла',
            subtitle: 'Каждые 10,000 км или 12 месяцев',
            status: 'soon',
            lastPerformed: '2023-12-15',
            lastMileage: 38500,
            nextDue: 48500,
            dueDate: '2024-12-15',
            currentMileage: 45300
        },
        {
            id: 2,
            title: '🔧 ТО-15000',
            subtitle: 'Каждые 15,000 км',
            status: 'overdue',
            lastPerformed: '2023-06-10',
            lastMileage: 30000,
            nextDue: 45000,
            dueDate: null,
            currentMileage: 45300
        },
        {
            id: 3,
            title: '🛡️ Замена тормозных колодок',
            subtitle: 'Каждые 30,000 км',
            status: 'ok',
            lastPerformed: '2023-11-20',
            lastMileage: 40000,
            nextDue: 70000,
            dueDate: null,
            currentMileage: 45300
        }
    ];
    
    res.json(maintenanceData);
});

// Списание бонусов
app.post('/api/redeem', (req, res) => {
    const { userId, amount, description } = req.body;
    
    // Здесь должна быть логика списания
    // Возвращаем успешный результат
    res.json({
        success: true,
        message: `Списано ${amount} бонусов`,
        newBalance: 2450 - amount
    });
});

// Загрузка SSL сертификатов
const options = {
    key: fs.readFileSync('key.pem'),
    cert: fs.readFileSync('cert.pem')
};

// Запуск HTTP сервера (редирект на HTTPS)
app.listen(PORT, () => {
    console.log(`🔄 HTTP сервер (редирект) запущен на порту ${PORT}`);
});

// Запуск HTTPS сервера
https.createServer(options, app).listen(HTTPS_PORT, () => {
    console.log(`🚀 HTTPS сервер Telegram Mini App запущен на порту ${HTTPS_PORT}`);
    console.log(`📱 Откройте приложение: https://localhost:${HTTPS_PORT}`);
    console.log(`🔗 Для Telegram WebApp используйте: https://your-domain.com:${HTTPS_PORT}`);
    console.log(`🛡️  Используется самоподписанный SSL сертификат`);
});
