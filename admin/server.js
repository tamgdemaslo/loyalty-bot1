const express = require('express');
const path = require('path');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();

const app = express();
const PORT = process.env.ADMIN_PORT || 3001;

// Подключение к базе данных
const db = new sqlite3.Database(path.join(__dirname, '..', 'loyalty.db'));

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Главная страница админ панели
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API Эндпоинты

// Получение статистики системы
app.get('/api/stats', (req, res) => {
    const queries = {
        totalUsers: 'SELECT COUNT(*) as count FROM user_map',
        totalBalance: 'SELECT SUM(balance) as total FROM bonuses',
        totalTransactions: 'SELECT COUNT(*) as count FROM bonus_transactions',
        totalSpent: 'SELECT SUM(total_spent) as total FROM loyalty_levels'
    };

    const stats = {};
    const promises = Object.keys(queries).map(key => {
        return new Promise((resolve, reject) => {
            db.get(queries[key], (err, row) => {
                if (err) reject(err);
                else {
                    stats[key] = row.count || row.total || 0;
                    resolve();
                }
            });
        });
    });

    Promise.all(promises)
        .then(() => {
            // Получение статистики по уровням
            db.all(`
                SELECT level_id, COUNT(*) as count 
                FROM loyalty_levels 
                GROUP BY level_id
                ORDER BY level_id
            `, (err, levelStats) => {
                if (err) {
                    console.error(err);
                    res.status(500).json({ error: 'Database error' });
                } else {
                    stats.levelDistribution = levelStats;
                    res.json(stats);
                }
            });
        })
        .catch(err => {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
        });
});

// Получение списка пользователей с пагинацией
app.get('/api/users', (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    const search = req.query.search || '';

    let query = `
        SELECT 
            u.tg_id,
            u.agent_id,
            u.phone,
            u.fullname,
            b.balance,
            l.level_id,
            l.total_spent,
            l.created_at as registered_at
        FROM user_map u
        LEFT JOIN bonuses b ON u.agent_id = b.agent_id
        LEFT JOIN loyalty_levels l ON u.agent_id = l.agent_id
    `;

    let countQuery = 'SELECT COUNT(*) as total FROM user_map u';
    let params = [];

    if (search) {
        query += ' WHERE (u.fullname LIKE ? OR u.phone LIKE ? OR u.agent_id LIKE ?)';
        countQuery += ' WHERE (u.fullname LIKE ? OR u.phone LIKE ? OR u.agent_id LIKE ?)';
        const searchParam = `%${search}%`;
        params = [searchParam, searchParam, searchParam];
    }

    query += ' ORDER BY l.created_at DESC LIMIT ? OFFSET ?';
    params.push(limit, offset);

    // Получаем общее количество записей
    db.get(countQuery, search ? [params[0], params[1], params[2]] : [], (err, countRow) => {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        // Получаем пользователей
        db.all(query, params, (err, users) => {
            if (err) {
                console.error(err);
                res.status(500).json({ error: 'Database error' });
                return;
            }

            res.json({
                users: users.map(user => ({
                    ...user,
                    balance: user.balance || 0,
                    level_id: user.level_id || 1,
                    total_spent: user.total_spent || 0
                })),
                pagination: {
                    page,
                    limit,
                    total: countRow.total,
                    pages: Math.ceil(countRow.total / limit)
                }
            });
        });
    });
});

// Получение детальной информации о пользователе
app.get('/api/users/:agentId', (req, res) => {
    const { agentId } = req.params;

    const userQuery = `
        SELECT 
            u.tg_id,
            u.agent_id,
            u.phone,
            u.fullname,
            b.balance,
            l.level_id,
            l.total_spent,
            l.created_at as registered_at,
            l.updated_at
        FROM user_map u
        LEFT JOIN bonuses b ON u.agent_id = b.agent_id
        LEFT JOIN loyalty_levels l ON u.agent_id = l.agent_id
        WHERE u.agent_id = ?
    `;

    db.get(userQuery, [agentId], (err, user) => {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        if (!user) {
            res.status(404).json({ error: 'User not found' });
            return;
        }

        // Получаем историю транзакций
        const transactionsQuery = `
            SELECT 
                transaction_type,
                amount,
                description,
                related_demand_id,
                created_at
            FROM bonus_transactions
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        `;

        db.all(transactionsQuery, [agentId], (err, transactions) => {
            if (err) {
                console.error(err);
                res.status(500).json({ error: 'Database error' });
                return;
            }

            res.json({
                user: {
                    ...user,
                    balance: user.balance || 0,
                    level_id: user.level_id || 1,
                    total_spent: user.total_spent || 0
                },
                transactions
            });
        });
    });
});

// Изменение баланса пользователя
app.post('/api/users/:agentId/balance', (req, res) => {
    const { agentId } = req.params;
    const { amount, description } = req.body;

    if (!amount || !description) {
        res.status(400).json({ error: 'Amount and description are required' });
        return;
    }

    const transactionType = amount > 0 ? 'accrual' : 'redemption';

    db.serialize(() => {
        // Обновляем баланс
        db.run(`
            INSERT INTO bonuses(agent_id, balance) VALUES(?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET balance = balance + ?
        `, [agentId, amount, amount], function(err) {
            if (err) {
                console.error(err);
                res.status(500).json({ error: 'Database error' });
                return;
            }

            // Добавляем транзакцию
            db.run(`
                INSERT INTO bonus_transactions (agent_id, transaction_type, amount, description)
                VALUES (?, ?, ?, ?)
            `, [agentId, transactionType, Math.abs(amount), description], function(err) {
                if (err) {
                    console.error(err);
                    res.status(500).json({ error: 'Database error' });
                    return;
                }

                // Получаем новый баланс
                db.get('SELECT balance FROM bonuses WHERE agent_id = ?', [agentId], (err, row) => {
                    if (err) {
                        console.error(err);
                        res.status(500).json({ error: 'Database error' });
                        return;
                    }

                    res.json({
                        success: true,
                        newBalance: row ? row.balance : 0,
                        transactionId: this.lastID
                    });
                });
            });
        });
    });
});

// Получение статистики по транзакциям
app.get('/api/transactions', (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 50;
    const offset = (page - 1) * limit;
    const type = req.query.type;
    const agentId = req.query.agent_id;

    let query = `
        SELECT 
            bt.id,
            bt.agent_id,
            bt.transaction_type,
            bt.amount,
            bt.description,
            bt.related_demand_id,
            bt.created_at,
            u.fullname,
            u.phone
        FROM bonus_transactions bt
        LEFT JOIN user_map u ON bt.agent_id = u.agent_id
    `;

    let countQuery = 'SELECT COUNT(*) as total FROM bonus_transactions bt';
    let params = [];
    let whereConditions = [];

    if (type) {
        whereConditions.push('bt.transaction_type = ?');
        params.push(type);
    }

    if (agentId) {
        whereConditions.push('bt.agent_id = ?');
        params.push(agentId);
    }

    if (whereConditions.length > 0) {
        const whereClause = ' WHERE ' + whereConditions.join(' AND ');
        query += whereClause;
        countQuery += whereClause;
    }

    query += ' ORDER BY bt.created_at DESC LIMIT ? OFFSET ?';
    params.push(limit, offset);

    // Получаем общее количество
    db.get(countQuery, type || agentId ? params.slice(0, -2) : [], (err, countRow) => {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        // Получаем транзакции
        db.all(query, params, (err, transactions) => {
            if (err) {
                console.error(err);
                res.status(500).json({ error: 'Database error' });
                return;
            }

            res.json({
                transactions,
                pagination: {
                    page,
                    limit,
                    total: countRow.total,
                    pages: Math.ceil(countRow.total / limit)
                }
            });
        });
    });
});

// ======= КЛИЕНТСКИЕ API ENDPOINTS =======

// Авторизация по номеру телефона
app.post('/api/auth/login', (req, res) => {
    const { phone } = req.body;
    
    if (!phone) {
        return res.status(400).json({ error: 'Phone number is required' });
    }

    const query = `
        SELECT 
            u.tg_id,
            u.agent_id,
            u.phone,
            u.fullname,
            b.balance,
            l.level_id,
            l.total_spent,
            l.created_at as registered_at
        FROM user_map u
        LEFT JOIN bonuses b ON u.agent_id = b.agent_id
        LEFT JOIN loyalty_levels l ON u.agent_id = l.agent_id
        WHERE u.phone = ?
    `;

    db.get(query, [phone], (err, user) => {
        if (err) {
            console.error(err);
            return res.status(500).json({ error: 'Database error' });
        }

        if (!user) {
            return res.status(404).json({ error: 'Пользователь не найден' });
        }

        res.json({
            success: true,
            user: {
                ...user,
                balance: user.balance || 0,
                level_id: user.level_id || 1,
                total_spent: user.total_spent || 0
            }
        });
    });
});

// Регистрация нового пользователя
app.post('/api/auth/register', (req, res) => {
    const { phone, fullname } = req.body;
    
    if (!phone || !fullname) {
        return res.status(400).json({ error: 'Phone and name are required' });
    }

    // Генерируем уникальный agent_id
    const agentId = `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    db.serialize(() => {
        // Создаем пользователя
        db.run(`
            INSERT INTO user_map (tg_id, agent_id, phone, fullname)
            VALUES (?, ?, ?, ?)
        `, [0, agentId, phone, fullname], function(err) {
            if (err) {
                console.error(err);
                return res.status(500).json({ error: 'Database error' });
            }

            // Создаем начальный баланс с приветственными бонусами
            db.run(`
                INSERT INTO bonuses (agent_id, balance) VALUES (?, 100)
            `, [agentId], (err) => {
                if (err) console.error('Error creating initial balance:', err);
            });

            // Создаем уровень лояльности
            db.run(`
                INSERT INTO loyalty_levels (agent_id, level_id, total_spent)
                VALUES (?, 1, 0)
            `, [agentId], (err) => {
                if (err) console.error('Error creating loyalty level:', err);
            });

            // Добавляем транзакцию приветственных бонусов
            db.run(`
                INSERT INTO bonus_transactions (agent_id, transaction_type, amount, description)
                VALUES (?, 'accrual', 100, 'Приветственные бонусы')
            `, [agentId], (err) => {
                if (err) console.error('Error creating welcome transaction:', err);
            });

            res.json({
                success: true,
                user: {
                    agent_id: agentId,
                    phone: phone,
                    fullname: fullname,
                    balance: 100,
                    level_id: 1,
                    total_spent: 0
                }
            });
        });
    });
});

// Получение отгрузок пользователя
app.get('/api/shipments/:agentId', (req, res) => {
    const { agentId } = req.params;
    
    // Пока возвращаем пустой массив, так как интеграция с МойСклад требует настройки
    res.json({
        success: true,
        shipments: [],
        message: 'История покупок будет доступна после настройки интеграции с МойСклад'
    });
});

// Получение услуг для записи
app.get('/api/booking/services', (req, res) => {
    // Возвращаем статичный список услуг
    const services = [
        { id: 1, name: 'Диагностика автомобиля', duration: 60, price: 1500 },
        { id: 2, name: 'Замена масла', duration: 30, price: 2500 },
        { id: 3, name: 'Шиномонтаж', duration: 45, price: 800 },
        { id: 4, name: 'Техническое обслуживание', duration: 120, price: 5000 }
    ];
    
    res.json({ success: true, services });
});

// Получение статистики по датам
app.get('/api/analytics/daily', (req, res) => {
    const days = parseInt(req.query.days) || 30;

    const query = `
        SELECT 
            DATE(created_at) as date,
            transaction_type,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM bonus_transactions
        WHERE created_at >= datetime('now', '-' || ? || ' days')
        GROUP BY DATE(created_at), transaction_type
        ORDER BY date DESC
    `;

    db.all(query, [days], (err, results) => {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        // Группируем по дням
        const analytics = {};
        results.forEach(row => {
            if (!analytics[row.date]) {
                analytics[row.date] = {
                    date: row.date,
                    accrual: { count: 0, amount: 0 },
                    redemption: { count: 0, amount: 0 }
                };
            }
            analytics[row.date][row.transaction_type] = {
                count: row.count,
                amount: row.total_amount
            };
        });

        res.json(Object.values(analytics));
    });
});

// Изменение уровня пользователя
app.post('/api/users/:agentId/level', (req, res) => {
    const { agentId } = req.params;
    const { levelId } = req.body;

    if (!levelId || levelId < 1 || levelId > 5) {
        res.status(400).json({ error: 'Valid level ID (1-5) is required' });
        return;
    }

    db.run(`
        UPDATE loyalty_levels 
        SET level_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE agent_id = ?
    `, [levelId, agentId], function(err) {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        if (this.changes === 0) {
            res.status(404).json({ error: 'User not found' });
            return;
        }

        res.json({ success: true });
    });
});

// Экспорт данных пользователей в CSV
app.get('/api/export/users', (req, res) => {
    const query = `
        SELECT 
            u.tg_id,
            u.agent_id,
            u.phone,
            u.fullname,
            b.balance,
            l.level_id,
            l.total_spent,
            l.created_at as registered_at
        FROM user_map u
        LEFT JOIN bonuses b ON u.agent_id = b.agent_id
        LEFT JOIN loyalty_levels l ON u.agent_id = l.agent_id
        ORDER BY l.created_at DESC
    `;

    db.all(query, [], (err, users) => {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        // Формируем CSV
        const headers = ['TG ID', 'Agent ID', 'Phone', 'Full Name', 'Balance', 'Level', 'Total Spent', 'Registered'];
        let csv = headers.join(',') + '\n';

        users.forEach(user => {
            const row = [
                user.tg_id,
                user.agent_id,
                user.phone || '',
                `"${user.fullname || ''}"`,
                user.balance || 0,
                user.level_id || 1,
                user.total_spent || 0,
                user.registered_at || ''
            ];
            csv += row.join(',') + '\n';
        });

        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', 'attachment; filename="users.csv"');
        res.send(csv);
    });
});

// Обработка ошибок
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Internal server error' });
});

// 404 обработчик
app.use((req, res) => {
    res.status(404).json({ error: 'Endpoint not found' });
});

app.listen(PORT, () => {
    console.log(`🔧 Админ панель запущена на порту ${PORT}`);
    console.log(`📊 Откройте панель: http://localhost:${PORT}`);
});

module.exports = app;
