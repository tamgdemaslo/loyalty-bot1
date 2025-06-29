// API интеграция Mini App с системой лояльности
const Database = require('better-sqlite3');
const path = require('path');

// Подключение к базе данных лояльности
const dbPath = path.join(__dirname, '..', 'loyalty.db');

// Проверяем существование базы данных и создаем при необходимости
let db;
try {
    db = new Database(dbPath);
    console.log('✅ База данных подключена:', dbPath);
} catch (error) {
    console.error('❌ Ошибка подключения к базе данных:', error);
    // Создаем новую базу данных
    db = new Database(dbPath);
    console.log('✅ Создана новая база данных:', dbPath);
}

// ВСЕГДА создаем таблицы при запуске (если их нет)
try {
    db.exec(`
        -- Таблица пользователей
        CREATE TABLE IF NOT EXISTS user_map (
            tg_id INTEGER PRIMARY KEY,
            agent_id TEXT NOT NULL,
            phone TEXT,
            fullname TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Таблица бонусов
        CREATE TABLE IF NOT EXISTS bonuses (
            agent_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0
        );
        
        -- Таблица транзакций бонусов
        CREATE TABLE IF NOT EXISTS bonus_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            description TEXT,
            related_demand_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Таблица уровней лояльности
        CREATE TABLE IF NOT EXISTS loyalty_levels (
            agent_id TEXT PRIMARY KEY,
            level_id INTEGER DEFAULT 1,
            total_spent INTEGER DEFAULT 0
        );
        
        -- Таблица истории обслуживания
        CREATE TABLE IF NOT EXISTS maintenance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            performed_date DATE NOT NULL,
            mileage INTEGER,
            source TEXT DEFAULT 'manual',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    `);
    console.log('✅ Базовые таблицы созданы/проверены');
    
    // Вставляем тестового пользователя для демо
    db.exec(`
        INSERT OR IGNORE INTO user_map (tg_id, agent_id, phone, fullname) 
        VALUES (123456789, 'test_agent_1', '+7900123456', 'Тестовый Пользователь');
        
        INSERT OR IGNORE INTO bonuses (agent_id, balance) 
        VALUES ('test_agent_1', 250000);
        
        INSERT OR IGNORE INTO loyalty_levels (agent_id, level_id, total_spent) 
        VALUES ('test_agent_1', 2, 1500000);
    `);
    console.log('✅ Тестовые данные добавлены');
} catch (initError) {
    console.error('❌ Ошибка инициализации таблиц:', initError);
}

class LoyaltyAPI {
    constructor() {
        this.db = db;
    }

    // Получить ID агента по Telegram ID
    getAgentId(telegramId) {
        try {
            const stmt = this.db.prepare("SELECT agent_id FROM user_map WHERE tg_id = ?");
            const row = stmt.get(telegramId);
            return Promise.resolve(row ? row.agent_id : null);
        } catch (error) {
            return Promise.reject(error);
        }
    }

    // Получить баланс пользователя
    getBalance(agentId) {
        try {
            const stmt = this.db.prepare("SELECT balance FROM bonuses WHERE agent_id = ?");
            const row = stmt.get(agentId);
            return Promise.resolve(row ? row.balance : 0);
        } catch (error) {
            return Promise.reject(error);
        }
    }

    // Получить уровень лояльности
    getLoyaltyLevel(agentId) {
        try {
            const stmt = this.db.prepare(`
                SELECT 
                    level_id,
                    total_spent,
                    COALESCE((
                        SELECT SUM(CASE WHEN transaction_type = 'accrual' THEN amount ELSE 0 END) 
                        FROM bonus_transactions WHERE agent_id = ?
                    ), 0) as total_earned,
                    COALESCE((
                        SELECT ABS(SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END))
                        FROM bonus_transactions WHERE agent_id = ?
                    ), 0) as total_redeemed
                FROM loyalty_levels 
                WHERE agent_id = ?
            `);
            const row = stmt.get(agentId, agentId, agentId);
            return Promise.resolve(row || { level_id: 1, total_earned: 0, total_redeemed: 0, total_spent: 0 });
        } catch (error) {
            return Promise.reject(error);
        }
    }

    // Получить транзакции пользователя
    getTransactions(agentId, limit = 20) {
        try {
            const stmt = this.db.prepare(`
                SELECT transaction_type, amount, description, created_at, related_demand_id
                FROM bonus_transactions 
                WHERE agent_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            `);
            const rows = stmt.all(agentId, limit);
            return Promise.resolve(rows || []);
        } catch (error) {
            return Promise.reject(error);
        }
    }

    // Получить данные ТО пользователя
    getMaintenanceData(agentId) {
        try {
            const stmt = this.db.prepare(`
                SELECT work_id, performed_date, mileage, source, notes, created_at
                FROM maintenance_history 
                WHERE agent_id = ? 
                ORDER BY performed_date DESC
            `);
            const rows = stmt.all(agentId);
            return Promise.resolve(rows || []);
        } catch (error) {
            return Promise.reject(error);
        }
    }

    // Получить контактную информацию пользователя
    getUserContact(telegramId) {
        try {
            const stmt = this.db.prepare("SELECT phone, fullname FROM user_map WHERE tg_id = ?");
            const row = stmt.get(telegramId);
            return Promise.resolve(row || { phone: null, fullname: null });
        } catch (error) {
            return Promise.reject(error);
        }
    }

    // Добавить транзакцию бонусов
    addBonusTransaction(agentId, transactionType, amount, description, demandId = null) {
        try {
            const stmt = this.db.prepare(`
                INSERT INTO bonus_transactions (agent_id, transaction_type, amount, description, related_demand_id, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            `);
            const result = stmt.run(agentId, transactionType, amount, description, demandId);
            return Promise.resolve(result.lastInsertRowid);
        } catch (error) {
            return Promise.reject(error);
        }
    }

    // Добавить запись о ТО
    addMaintenanceRecord(agentId, workId, performedDate, mileage, notes = '') {
        try {
            const stmt = this.db.prepare(`
                INSERT INTO maintenance_history (agent_id, work_id, performed_date, mileage, source, notes, created_at)
                VALUES (?, ?, ?, ?, 'manual', ?, datetime('now'))
            `);
            const result = stmt.run(agentId, workId, performedDate, mileage, notes);
            return Promise.resolve(result.lastInsertRowid);
        } catch (error) {
            return Promise.reject(error);
        }
    }

    // Получить последние посещения (через МойСклад API)
    async getRecentVisits(agentId, limit = 10) {
        try {
            // Здесь должен быть вызов к МойСклад API
            // Для демо возвращаем моковые данные
            const visits = [
                {
                    id: 1,
                    name: '12345',
                    moment: '2024-01-20T14:30:00Z',
                    sum: 8500,
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
                    name: '12344', 
                    moment: '2024-01-15T11:15:00Z',
                    sum: 15300,
                    services: ['ТО-15000', 'Замена фильтров'],
                    car: {
                        model: 'Toyota Camry',
                        vin: 'JT2BF28K6X0123456',
                        mileage: 45000
                    },
                    bonusEarned: 765
                }
            ];
            
            return visits.slice(0, limit);
        } catch (error) {
            console.error('Error fetching visits:', error);
            return [];
        }
    }

    // Получить статистику клиента
    async getClientStatistics(agentId) {
        try {
            const visits = await this.getRecentVisits(agentId, 100);
            const transactions = await this.getTransactions(agentId, 100);
            const loyaltyData = await this.getLoyaltyLevel(agentId);
            
            const totalVisits = visits.length;
            const totalSpent = loyaltyData.total_spent;
            const totalEarned = loyaltyData.total_earned;
            const totalRedeemed = Math.abs(loyaltyData.total_redeemed);
            
            const currentYear = new Date().getFullYear();
            const thisYearVisits = visits.filter(v => 
                new Date(v.moment).getFullYear() === currentYear
            ).length;
            
            const averageCheck = totalVisits > 0 ? totalSpent / totalVisits : 0;
            
            return {
                totalVisits,
                totalSpent,
                totalEarned,
                totalRedeemed,
                thisYearVisits,
                averageCheck,
                loyaltyLevel: loyaltyData.level_id
            };
        } catch (error) {
            console.error('Error getting client statistics:', error);
            throw error;
        }
    }
}

module.exports = LoyaltyAPI;
