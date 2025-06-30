const express = require('express');
const https = require('https');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const crypto = require('crypto');
const loyaltyAPI = require('./api_postgres');

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
app.post('/api/user', async (req, res) => {
    const { initData, user: directUser } = req.body;
    console.log('--- Received /api/user request ---');

    try {
        let user = null;

        // Extract user data from initData or directUser
        if (directUser && directUser.id) {
            user = directUser;
        } else if (initData) {
            const urlParams = new URLSearchParams(initData);
            const userParam = urlParams.get('user');
            if (userParam) {
                try {
                    user = JSON.parse(decodeURIComponent(userParam));
                } catch (e) {
                     console.error('Failed to parse user data from initData', e);
                }
            }
        }

        // If no user data, force phone auth
        if (!user || !user.id) {
            console.log('User ID not found in initData, requires phone auth.');
            return res.status(404).json({
                error: 'Phone authorization required',
                requiresPhoneAuth: true,
                firstName: 'пользователь'
            });
        }
        
        console.log(`User found in initData: ${user.id} (${user.first_name})`);

        // Check if user is mapped in our DB
        const agentId = await loyaltyAPI.getAgentId(user.id);

        if (!agentId) {
            // User is in Telegram, but not mapped in our DB yet.
            console.log(`User ${user.id} not found in DB, requires phone auth.`);
            return res.status(404).json({
                error: 'User not registered, phone authorization required',
                requiresPhoneAuth: true,
                firstName: user.first_name || 'пользователь'
            });
        }

        // User is registered! Fetch all data and return it.
        console.log(`User ${user.id} is mapped to agent ${agentId}. Fetching full data...`);
        const [balance, loyaltyLevel, contact, statistics] = await Promise.all([
            loyaltyAPI.getBalance(agentId),
            loyaltyAPI.getLoyaltyLevel(agentId),
            loyaltyAPI.getUserContact(user.id),
            loyaltyAPI.getClientStatistics(agentId)
        ]);

        const levelNames = ['', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'];
        const levelName = levelNames[loyaltyLevel.level_id] || 'Bronze';

        const userData = {
            id: user.id,
            name: contact.fullname || user.first_name || 'Пользователь',
            phone: contact.phone,
            balance: Math.round(balance / 100),
            level: levelName,
            levelId: loyaltyLevel.level_id,
            totalSpent: Math.round(loyaltyLevel.total_spent / 100),
            totalEarned: Math.round(loyaltyLevel.total_earned / 100),
            totalRedeemed: Math.round(loyaltyLevel.total_redeemed / 100),
            totalVisits: statistics.totalVisits,
            thisYearVisits: statistics.thisYearVisits,
            averageCheck: Math.round(statistics.averageCheck / 100),
            registeredDate: new Date().toISOString().split('T')[0], // Placeholder
            isNewUser: false
        };

        console.log('Successfully fetched user data. Returning 200 OK.');
        res.json(userData);

    } catch (error) {
        console.error('Error in /api/user:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Получение истории посещений
app.get('/api/visits/:userId', async (req, res) => {
    const { userId } = req.params;
    
    try {
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
        // Получаем ID агента по Telegram ID
        const agentId = await loyaltyAPI.getAgentId(parseInt(userId));
        if (!agentId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Получаем данные о ТО
        const maintenanceData = await loyaltyAPI.getMaintenanceStatus(agentId);
        
        // Форматируем данные для фронтенда
        const formattedData = maintenanceData.map(item => ({
            id: item.work_id,
            title: item.work_info.name,
            subtitle: `Каждые ${item.mileage_interval} км или ${item.time_interval} месяцев`,
            status: item.status,  // 'ok', 'soon', 'overdue', 'never_done'
            lastPerformed: item.last_maintenance ? item.last_maintenance.date.split('T')[0] : null,
            lastMileage: item.last_maintenance ? item.last_maintenance.mileage : 0,
            nextDue: item.next_mileage || 0,
            dueDate: item.next_date ? item.next_date.split('T')[0] : null,
            currentMileage: item.current_mileage || 0,
            message: item.message
        }));
        
        res.json(formattedData);
    } catch (error) {
        console.error('Error getting maintenance data:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Списание бонусов
app.post('/api/redeem', async (req, res) => {
    const { userId, amount, description } = req.body;
    
    try {
        // Получаем ID агента по Telegram ID
        const agentId = await loyaltyAPI.getAgentId(parseInt(userId));
        if (!agentId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Проверяем достаточно ли бонусов
        const currentBalance = await loyaltyAPI.getBalance(agentId);
        const amountInCents = amount * 100; // Переводим в копейки
        
        if (currentBalance < amountInCents) {
            return res.status(400).json({
                error: 'Insufficient balance',
                message: 'Недостаточно бонусов для списания'
            });
        }
        
        // Списываем бонусы
        const success = await loyaltyAPI.changeBalance(agentId, -amountInCents);
        if (!success) {
            return res.status(500).json({
                error: 'Failed to redeem bonuses',
                message: 'Не удалось списать бонусы'
            });
        }
        
        // Добавляем запись о транзакции
        await loyaltyAPI.addBonusTransaction(
            agentId,
            'redemption',
            -amountInCents,
            description || 'Списание бонусов в приложении'
        );
        
        // Получаем новый баланс
        const newBalance = await loyaltyAPI.getBalance(agentId);
        
        res.json({
            success: true,
            message: `Списано ${amount} бонусов`,
            newBalance: Math.round(newBalance / 100) // Возвращаем в рублях
        });
    } catch (error) {
        console.error('Error redeeming bonuses:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
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
