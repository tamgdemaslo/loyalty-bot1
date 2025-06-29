// API интеграция Mini App с системой лояльности
const Database = require('better-sqlite3');
const path = require('path');

// Подключение к базе данных лояльности
const dbPath = path.join(__dirname, '..', 'loyalty.db');

// Создаем подключение к базе данных
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

// Создаем таблицы при запуске (если их нет)
try {
    // Создаем таблицы
    db.exec(`CREATE TABLE IF NOT EXISTS user_mapping (
        tg_id INTEGER PRIMARY KEY,
        agent_id TEXT NOT NULL,
        phone TEXT,
        fullname TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    
    db.exec(`CREATE TABLE IF NOT EXISTS balances (
        agent_id TEXT PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )`);
    
    db.exec(`CREATE TABLE IF NOT EXISTS bonus_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        operation_type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        description TEXT,
        related_demand_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    
    db.exec(`CREATE TABLE IF NOT EXISTS loyalty_levels (
        agent_id TEXT PRIMARY KEY,
        level_id INTEGER DEFAULT 1,
        total_spent INTEGER DEFAULT 0,
        total_earned INTEGER DEFAULT 0,
        total_redeemed INTEGER DEFAULT 0
    )`);
    
    db.exec(`CREATE TABLE IF NOT EXISTS maintenance_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        work_id TEXT NOT NULL,
        performed_date DATE NOT NULL,
        mileage INTEGER,
        source TEXT DEFAULT 'manual',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);
    
    console.log('✅ Базовые таблицы созданы/проверены');
    
    // Вставляем тестового пользователя для демо
    const insertUser = db.prepare(`INSERT OR IGNORE INTO user_mapping (tg_id, agent_id, phone, fullname) VALUES (?, ?, ?, ?)`);
    insertUser.run(12345, 'demo_agent_id', '+7123456789', 'Demo User');
    
    const insertBalance = db.prepare(`INSERT OR IGNORE INTO balances (agent_id, balance) VALUES (?, ?)`);
    insertBalance.run('demo_agent_id', 245000); // 2450 рублей в копейках
    
    const insertLoyalty = db.prepare(`INSERT OR IGNORE INTO loyalty_levels (agent_id, level_id, total_spent, total_earned, total_redeemed) VALUES (?, ?, ?, ?, ?)`);
    insertLoyalty.run('demo_agent_id', 2, 7500000, 542000, 297000); // Все в копейках
    
    console.log('✅ Тестовые данные добавлены');
} catch (error) {
    console.error('❌ Ошибка создания таблиц:', error);
}

class LoyaltyAPI {
    constructor() {
        this.db = db;
    }

    // Получить ID агента по Telegram ID
    async getAgentId(telegramId) {
        try {
            const stmt = this.db.prepare("SELECT agent_id FROM user_mapping WHERE tg_id = ?");
            const row = stmt.get(telegramId);
            return row ? row.agent_id : null;
        } catch (error) {
            console.error('Error getting agent ID:', error);
            return null;
        }
    }

    // Получить баланс пользователя
    async getBalance(agentId) {
        try {
            const stmt = this.db.prepare("SELECT balance FROM balances WHERE agent_id = ?");
            const row = stmt.get(agentId);
            return row ? row.balance : 0;
        } catch (error) {
            console.error('Error getting balance:', error);
            return 0;
        }
    }

    // Получить уровень лояльности
    getLoyaltyLevel(agentId) {
        return new Promise((resolve, reject) => {
            const query = `
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
            `;
            this.db.get(query, [agentId, agentId, agentId], (err, row) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(row || { level_id: 1, total_earned: 0, total_redeemed: 0, total_spent: 0 });
                }
            });
        });
    }

    // Получить транзакции пользователя
    getTransactions(agentId, limit = 20) {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT transaction_type, amount, description, created_at, related_demand_id
                FROM bonus_transactions 
                WHERE agent_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            `;
            this.db.all(query, [agentId, limit], (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows || []);
                }
            });
        });
    }

    // Получить данные ТО пользователя
    getMaintenanceData(agentId) {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT work_id, performed_date, mileage, source, notes, created_at
                FROM maintenance_history 
                WHERE agent_id = ? 
                ORDER BY performed_date DESC
            `;
            this.db.all(query, [agentId], (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows || []);
                }
            });
        });
    }

    // Получить контактную информацию пользователя
    getUserContact(telegramId) {
        return new Promise((resolve, reject) => {
            this.db.get("SELECT phone, fullname FROM user_map WHERE tg_id = ?", [telegramId], (err, row) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(row || { phone: null, fullname: null });
                }
            });
        });
    }

    // Добавить транзакцию бонусов
    addBonusTransaction(agentId, transactionType, amount, description, demandId = null) {
        return new Promise((resolve, reject) => {
            const query = `
                INSERT INTO bonus_transactions (agent_id, transaction_type, amount, description, related_demand_id, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            `;
            this.db.run(query, [agentId, transactionType, amount, description, demandId], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve(this.lastID);
                }
            });
        });
    }

    // Добавить запись о ТО
    addMaintenanceRecord(agentId, workId, performedDate, mileage, notes = '') {
        return new Promise((resolve, reject) => {
            const query = `
                INSERT INTO maintenance_history (agent_id, work_id, performed_date, mileage, source, notes, created_at)
                VALUES (?, ?, ?, ?, 'manual', ?, datetime('now'))
            `;
            this.db.run(query, [agentId, workId, performedDate, mileage, notes], function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve(this.lastID);
                }
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

    // Поиск контрагента в МойСклад по номеру телефона
    async findAgentByPhone(phone) {
        try {
            // Здесь должен быть настоящий вызов к МойСклад API
            // Для демо возвращаем моковые данные
            
            // Очищаем номер телефона от лишних символов
            const cleanPhone = phone.replace(/[^\d]/g, '');
            
            // Имитируем поиск в МойСклад
            console.log(`🔍 Searching for agent with phone: ${cleanPhone}`);
            
            // Моковая логика: если номер содержит '123', то пользователь найден
            if (cleanPhone.includes('123')) {
                return 'existing_agent_' + cleanPhone.slice(-6);
            }
            
            return null; // Пользователь не найден в МойСклад
        } catch (error) {
            console.error('Error finding agent by phone:', error);
            throw error;
        }
    }

    // Создание нового контрагента в МойСклад
    async createNewAgent(name, phone) {
        try {
            // Здесь должен быть настоящий вызов к МойСклад API
            // Для демо генерируем фейковый ID
            
            console.log(`👤 Creating new agent in MoySklad: ${name}, ${phone}`);
            
            const agentId = 'new_agent_' + Date.now();
            
            // Моковая задержка API
            await new Promise(resolve => setTimeout(resolve, 500));
            
            console.log(`✅ Agent created with ID: ${agentId}`);
            
            return agentId;
        } catch (error) {
            console.error('Error creating new agent:', error);
            throw error;
        }
    }

    // Регистрация связи пользователя
    async registerUserMapping(telegramId, agentId, phone, fullname) {
        return new Promise((resolve, reject) => {
            // Сначала пытаемся вставить нового пользователя
            const insertQuery = `
                INSERT OR REPLACE INTO user_map (tg_id, agent_id, phone, fullname, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            `;
            
            this.db.run(insertQuery, [telegramId, agentId, phone, fullname], function(err) {
                if (err) {
                    console.error('Error inserting user mapping:', err);
                    reject(err);
                    return;
                }
                
                console.log(`✅ User mapping created: TG=${telegramId} -> Agent=${agentId}`);
                
                // Создаем запись в таблице бонусов если её нет
                const bonusQuery = `
                    INSERT OR IGNORE INTO bonuses (agent_id, balance)
                    VALUES (?, 10000)
                `;
                
                this.db.run(bonusQuery, [agentId], function(bonusErr) {
                    if (bonusErr) {
                        console.error('Error creating bonus record:', bonusErr);
                    }
                    
                    // Создаем запись уровня лояльности если её нет
                    const loyaltyQuery = `
                        INSERT OR IGNORE INTO loyalty_levels (agent_id, level_id, total_spent)
                        VALUES (?, 1, 0)
                    `;
                    
                    this.db.run(loyaltyQuery, [agentId], function(loyaltyErr) {
                        if (loyaltyErr) {
                            console.error('Error creating loyalty record:', loyaltyErr);
                        }
                        
                        resolve(this.lastID || this.changes);
                    });
                });
            });
        });
    }

    // Обновление баланса пользователя
    async updateBalance(agentId, deltaAmount) {
        return new Promise((resolve, reject) => {
            const updateQuery = `
                UPDATE bonuses 
                SET balance = balance + ? 
                WHERE agent_id = ?
            `;
            
            this.db.run(updateQuery, [deltaAmount, agentId], function(err) {
                if (err) {
                    console.error('Error updating balance:', err);
                    reject(err);
                    return;
                }
                
                // Если записи нет, создаем её
                if (this.changes === 0) {
                    const insertQuery = `
                        INSERT INTO bonuses (agent_id, balance)
                        VALUES (?, ?)
                    `;
                    
                    db.run(insertQuery, [agentId, deltaAmount], function(insertErr) {
                        if (insertErr) {
                            console.error('Error inserting balance record:', insertErr);
                            reject(insertErr);
                        } else {
                            console.log(`💰 Balance created for ${agentId}: ${deltaAmount > 0 ? '+' : ''}${deltaAmount / 100}₽`);
                            resolve(true);
                        }
                    });
                } else {
                    console.log(`💰 Balance updated for ${agentId}: ${deltaAmount > 0 ? '+' : ''}${deltaAmount / 100}₽`);
                    resolve(true);
                }
            });
        });
    }
}

module.exports = LoyaltyAPI;
