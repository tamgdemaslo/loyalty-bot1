const fs = require('fs');
const path = require('path');

class LoyaltyAPI {
    constructor() {
        // Путь к JSON файлу
        this.dataPath = path.join(__dirname, 'loyalty_data.json');
        this.data = this.loadData();
    }

    loadData() {
        try {
            if (fs.existsSync(this.dataPath)) {
                const data = fs.readFileSync(this.dataPath, 'utf8');
                return JSON.parse(data);
            }
        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
        }
        
        // Возвращаем структуру по умолчанию с демо данными
        return {
            agents: {
                'agent1': {
                    id: 'agent1',
                    name: 'Иван Петров',
                    phone: '+7 999 123-45-67',
                    telegram_id: 123456789,
                    created_at: '2023-05-15T10:00:00.000Z'
                }
            },
            loyalty_levels: {
                'agent1': {
                    level_id: 2,
                    total_spent: 7500000, // в копейках (75,000 рублей)
                    total_earned: 542000, // в копейках (5,420 рублей)
                    total_redeemed: 297000 // в копейках (2,970 рублей)
                }
            },
            bonuses: {
                'agent1': {
                    balance: 245000, // в копейках (2,450 рублей)
                    last_updated: '2024-01-20T14:30:00.000Z'
                }
            },
            bonus_transactions: [
                {
                    id: 1,
                    agent_id: 'agent1',
                    transaction_type: 'visit',
                    amount: 45000, // 450 рублей
                    description: 'Начисление за визит №12345',
                    related_demand_id: 'visit1',
                    created_at: '2024-01-20 14:30:00'
                },
                {
                    id: 2,
                    agent_id: 'agent1',
                    transaction_type: 'redemption',
                    amount: -32000, // -320 рублей
                    description: 'Списание бонусов',
                    related_demand_id: null,
                    created_at: '2024-01-18 16:15:00'
                },
                {
                    id: 3,
                    agent_id: 'agent1',
                    transaction_type: 'visit',
                    amount: 68000, // 680 рублей
                    description: 'Начисление за визит №12344',
                    related_demand_id: 'visit2',
                    created_at: '2024-01-15 11:45:00'
                }
            ],
            contacts: {
                'contact1': {
                    id: 'contact1',
                    agent_id: 'agent1',
                    telegram_id: 123456789,
                    fullname: 'Иван Петров',
                    phone: '+7 999 123-45-67',
                    email: 'ivan.petrov@example.com',
                    created_at: '2023-05-15T10:00:00.000Z'
                }
            },
            maintenance_records: [
                {
                    id: 1,
                    agent_id: 'agent1',
                    work_id: 'oil_change',
                    performed_date: '2024-01-10',
                    mileage: 45000,
                    notes: 'Замена масла Mobil 1',
                    created_at: '2024-01-10T09:00:00.000Z'
                }
            ],
            nextTransactionId: 4
        };
    }
    
    saveData() {
        try {
            fs.writeFileSync(this.dataPath, JSON.stringify(this.data, null, 2));
        } catch (error) {
            console.error('Ошибка сохранения данных:', error);
        }
    }

    async getAgentId(telegramId) {
        // Ищем агента по telegram_id
        for (const [agentId, agent] of Object.entries(this.data.agents)) {
            if (agent.telegram_id === telegramId) {
                return agentId;
            }
        }
        return null;
    }

    async getBalance(agentId) {
        return this.data.bonuses[agentId]?.balance || 0;
    }

    async getLoyaltyLevel(agentId) {
        const level = this.data.loyalty_levels[agentId];
        
        if (level) {
            return level;
        }
        
        // Если записи нет, создаем с уровнем 1
        return {
            level_id: 1,
            total_spent: 0,
            total_earned: 0,
            total_redeemed: 0
        };
    }

    async getUserContact(telegramId) {
        // Ищем контакт по telegram_id
        for (const contact of Object.values(this.data.contacts)) {
            if (contact.telegram_id === telegramId) {
                return contact;
            }
        }
        
        return {
            fullname: 'Клиент',
            phone: 'Не указан',
            email: null
        };
    }

    async getClientStatistics(agentId) {
        // Считаем посещения из транзакций
        const visitTransactions = this.data.bonus_transactions.filter(
            t => t.agent_id === agentId && t.transaction_type === 'visit'
        );
        
        const currentYear = new Date().getFullYear();
        const thisYearVisits = visitTransactions.filter(t => {
            const transactionYear = new Date(t.created_at).getFullYear();
            return transactionYear === currentYear;
        });
        
        // Считаем средний чек из loyalty_levels
        const loyaltyLevel = await this.getLoyaltyLevel(agentId);
        const averageCheck = loyaltyLevel.total_spent > 0 && visitTransactions.length > 0 
            ? Math.round(loyaltyLevel.total_spent / visitTransactions.length)
            : 0;
        
        return {
            totalVisits: visitTransactions.length || 0,
            thisYearVisits: thisYearVisits.length || 0,
            averageCheck: averageCheck
        };
    }

    async getRecentVisits(agentId, limit = 10) {
        // Демо данные о посещениях
        const visits = [
            {
                id: 'visit1',
                name: '12345',
                sum: 850000, // в копейках
                moment: '2024-01-20T10:30:00',
                services: [
                    { name: 'Замена масла' },
                    { name: 'Диагностика двигателя' }
                ],
                car: {
                    model: 'Toyota Camry',
                    year: 2019
                },
                bonusEarned: 42500 // в копейках
            },
            {
                id: 'visit2', 
                name: '12344',
                sum: 1530000,
                moment: '2024-01-15T14:15:00',
                services: [
                    { name: 'ТО-15000' },
                    { name: 'Замена фильтров' }
                ],
                car: {
                    model: 'Toyota Camry',
                    year: 2019
                },
                bonusEarned: 76500
            },
            {
                id: 'visit3',
                name: '12343',
                sum: 320000,
                moment: '2024-01-10T16:20:00',
                services: [
                    { name: 'Развал-схождение' }
                ],
                car: {
                    model: 'Toyota Camry',
                    year: 2019
                },
                bonusEarned: 16000
            }
        ];
        
        return visits.slice(0, limit);
    }

    async getTransactions(agentId, limit = 20) {
        const transactions = this.data.bonus_transactions
            .filter(t => t.agent_id === agentId)
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, limit);
        
        return transactions;
    }

    async addBonusTransaction(agentId, type, amount, description, relatedDemandId = null) {
        const transaction = {
            id: this.data.nextTransactionId++,
            agent_id: agentId,
            transaction_type: type,
            amount: amount,
            description: description,
            related_demand_id: relatedDemandId,
            created_at: new Date().toISOString().replace('T', ' ').substr(0, 19)
        };
        
        this.data.bonus_transactions.push(transaction);
        this.saveData();
        return transaction.id;
    }

    async getMaintenanceData(agentId) {
        const records = this.data.maintenance_records
            .filter(r => r.agent_id === agentId)
            .sort((a, b) => new Date(b.performed_date) - new Date(a.performed_date));
        
        return records;
    }

    // Обновление баланса
    async updateBalance(agentId, amount) {
        if (!this.data.bonuses[agentId]) {
            this.data.bonuses[agentId] = { balance: 0, last_updated: new Date().toISOString() };
        }
        
        this.data.bonuses[agentId].balance += amount;
        this.data.bonuses[agentId].last_updated = new Date().toISOString();
        this.saveData();
    }
}

module.exports = LoyaltyAPI;
