// API интеграция Mini App с системой лояльности
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Подключение к базе данных лояльности
const dbPath = path.join(__dirname, '..', 'loyalty.db');
const db = new sqlite3.Database(dbPath);

class LoyaltyAPI {
    constructor() {
        this.db = db;
    }

    // Получить ID агента по Telegram ID
    getAgentId(telegramId) {
        return new Promise((resolve, reject) => {
            this.db.get(
                "SELECT agent_id FROM user_map WHERE tg_id = ?",
                [telegramId],
                (err, row) => {
                    if (err) reject(err);
                    else resolve(row ? row.agent_id : null);
                }
            );
        });
    }

    // Получить баланс пользователя
    getBalance(agentId) {
        return new Promise((resolve, reject) => {
            this.db.get(
                "SELECT balance FROM bonuses WHERE agent_id = ?",
                [agentId],
                (err, row) => {
                    if (err) reject(err);
                    else resolve(row ? row.balance : 0);
                }
            );
        });
    }

    // Получить уровень лояльности
    getLoyaltyLevel(agentId) {
        return new Promise((resolve, reject) => {
            this.db.get(`
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
            `, [agentId, agentId, agentId], (err, row) => {
                if (err) reject(err);
                else resolve(row || { level_id: 1, total_earned: 0, total_redeemed: 0, total_spent: 0 });
            });
        });
    }

    // Получить транзакции пользователя
    getTransactions(agentId, limit = 20) {
        return new Promise((resolve, reject) => {
            this.db.all(`
                SELECT transaction_type, amount, description, created_at, related_demand_id
                FROM bonus_transactions 
                WHERE agent_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            `, [agentId, limit], (err, rows) => {
                if (err) reject(err);
                else resolve(rows || []);
            });
        });
    }

    // Получить данные ТО пользователя
    getMaintenanceData(agentId) {
        return new Promise((resolve, reject) => {
            this.db.all(`
                SELECT work_id, performed_date, mileage, source, notes, created_at
                FROM maintenance_history 
                WHERE agent_id = ? 
                ORDER BY performed_date DESC
            `, [agentId], (err, rows) => {
                if (err) reject(err);
                else resolve(rows || []);
            });
        });
    }

    // Получить контактную информацию пользователя
    getUserContact(telegramId) {
        return new Promise((resolve, reject) => {
            this.db.get(
                "SELECT phone, fullname FROM user_map WHERE tg_id = ?",
                [telegramId],
                (err, row) => {
                    if (err) reject(err);
                    else resolve(row || { phone: null, fullname: null });
                }
            );
        });
    }

    // Добавить транзакцию бонусов
    addBonusTransaction(agentId, transactionType, amount, description, demandId = null) {
        return new Promise((resolve, reject) => {
            this.db.run(`
                INSERT INTO bonus_transactions (agent_id, transaction_type, amount, description, related_demand_id, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            `, [agentId, transactionType, amount, description, demandId], function(err) {
                if (err) reject(err);
                else resolve(this.lastID);
            });
        });
    }

    // Добавить запись о ТО
    addMaintenanceRecord(agentId, workId, performedDate, mileage, notes = '') {
        return new Promise((resolve, reject) => {
            this.db.run(`
                INSERT INTO maintenance_history (agent_id, work_id, performed_date, mileage, source, notes, created_at)
                VALUES (?, ?, ?, ?, 'manual', ?, datetime('now'))
            `, [agentId, workId, performedDate, mileage, notes], function(err) {
                if (err) reject(err);
                else resolve(this.lastID);
            });
        });
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
