require('dotenv').config();
const express = require('express');
const path = require('path');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

// Инициализация ботов с обработкой ошибок
let telegramBot = null;
let whatsappClient = null;

// Инициализация Telegram бота
if (process.env.TELEGRAM_BOT_TOKEN && process.env.TELEGRAM_BOT_TOKEN !== 'your_telegram_bot_token_here') {
  try {
    telegramBot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: false });
    console.log('✅ Telegram бот инициализирован');
  } catch (error) {
    console.error('❌ Ошибка инициализации Telegram бота:', error.message);
  }
} else {
  console.log('⚠️ Telegram бот не настроен - укажите TELEGRAM_BOT_TOKEN в .env файле');
}

// Инициализация SMS.RU клиента
if (process.env.SMSRU_API_ID && process.env.SMSRU_API_ID !== 'your_smsru_api_id_here') {
  console.log('✅ SMS.RU клиент инициализирован');
} else {
  console.log('⚠️ SMS.RU клиент не настроен - укажите SMSRU_API_ID в .env файле');
}

function sendTelegramMessage(chatId, message) {
  if (!telegramBot) {
    console.log('⚠️ Telegram бот не настроен, сообщение не отправлено');
    return Promise.resolve(false);
  }
  
  return telegramBot.sendMessage(chatId, message)
    .then(() => {
      console.log(`✅ Telegram сообщение отправлено пользователю ${chatId}`);
      return true;
    })
    .catch(error => {
      console.error(`❌ Ошибка отправки Telegram сообщения пользователю ${chatId}:`, error.message);
      return false;
    });
}

// Функция для отправки SMS через SMS.RU
async function sendSMSMessage(to, message) {
  if (!process.env.SMSRU_API_ID || process.env.SMSRU_API_ID === 'your_smsru_api_id_here') {
    console.log('⚠️ SMS.RU не настроен, сообщение не отправлено');
    return false;
  }
  
  try {
    // Очищаем номер телефона от лишних символов
    const cleanPhone = to.replace(/[^\d]/g, '');
    
    const response = await axios.post('https://sms.ru/sms/send', {
      api_id: process.env.SMSRU_API_ID,
      to: cleanPhone,
      msg: message,
      json: 1
    });
    
    if (response.data && response.data.status === 'OK') {
      console.log(`✅ SMS отправлено на ${to} через SMS.RU`);
      return true;
    } else {
      console.error(`❌ Ошибка SMS.RU:`, response.data);
      return false;
    }
  } catch (error) {
    console.error(`❌ Ошибка отправки SMS на ${to}:`, error.message);
    return false;
  }
}

// Функция для отправки WhatsApp через SMS.RU (если поддерживается)
async function sendWhatsAppMessage(to, message) {
  if (!process.env.SMSRU_API_ID || process.env.SMSRU_API_ID === 'your_smsru_api_id_here') {
    console.log('⚠️ SMS.RU не настроен, WhatsApp сообщение не отправлено');
    return false;
  }
  
  try {
    // Попробуем отправить как SMS, так как не все российские сервисы поддерживают WhatsApp API
    return await sendSMSMessage(to, message);
  } catch (error) {
    console.error(`❌ Ошибка отправки WhatsApp сообщения на ${to}:`, error.message);
    return false;
  }
}

// Константы для МойСклад API
const MS_BASE = 'https://api.moysklad.ru/api/remap/1.2';
const MS_HEADERS = {
    'Authorization': `Bearer ${process.env.MS_TOKEN || ''}`,
    'Content-Type': 'application/json',
    'Accept': 'application/json;charset=utf-8'
};

// Вспомогательные функции для работы с атрибутами
function getAttributeValue(attributes, name) {
    const attr = attributes.find(a => a.name === name);
    return attr ? attr.value : null;
}

function getAssortmentAttribute(assortment, name) {
    const attributes = assortment.attributes || [];
    return getAttributeValue(attributes, name);
}

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
// Проверка готовности очередей
app.get('/api/call-queues/status', (req, res) => {
    res.json({
        message: 'Очереди готовы к работе! Нужна ли дополнительная настройка или анализ?'
    });
});

// Получение статистики очередей обзвона
app.get('/api/call-queues/stats', (req, res) => {
    const query = `
        SELECT 
            queue_type,
            COUNT(*) as count,
            AVG(avg_check) as avg_check,
            SUM(total_revenue) as total_revenue,
            AVG(recency_days) as avg_recency
        FROM call_queues
        WHERE is_active = 1
        GROUP BY queue_type
    `;
    
    db.all(query, [], (err, stats) => {
        if (err) {
            console.error('Error loading queue stats:', err);
            res.status(500).json({ error: 'Database error' });
            return;
        }
        
        res.json({
            stats: stats || [],
            lastUpdated: new Date().toISOString()
        });
    });
});

// Получение списка клиентов из очереди
app.get('/api/call-queues/:queueType', (req, res) => {
    const { queueType } = req.params;
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    
    // Получаем общее количество
    const countQuery = `
        SELECT COUNT(*) as total 
        FROM call_queues 
        WHERE queue_type = ? AND is_active = 1
    `;
    
    db.get(countQuery, [queueType], (err, countRow) => {
        if (err) {
            console.error('Error counting queue items:', err);
            res.status(500).json({ error: 'Database error' });
            return;
        }
        
        // Получаем клиентов с полной информацией
        const query = `
            SELECT 
                cq.*,
                cd.name,
                cd.phone,
                cd.email,
                cd.description,
                b.balance as bonus_balance,
                u.tg_id,
                cs.segment,
                cs.activity_status,
                cs.last_purchase_date,
                (
                    SELECT COUNT(*) 
                    FROM contact_history ch 
                    WHERE ch.agent_id = cq.agent_id 
                    AND ch.contact_type = 'call'
                ) as call_count,
                (
                    SELECT MAX(contact_date) 
                    FROM contact_history ch 
                    WHERE ch.agent_id = cq.agent_id
                ) as last_contact
            FROM call_queues cq
            LEFT JOIN contractors_data cd ON cq.agent_id = cd.agent_id
            LEFT JOIN bonuses b ON cq.agent_id = b.agent_id
            LEFT JOIN user_map u ON cq.agent_id = u.agent_id
            LEFT JOIN customer_segments cs ON cq.agent_id = cs.agent_id
            WHERE cq.queue_type = ? AND cq.is_active = 1
            ORDER BY cq.priority ASC, cq.score DESC
            LIMIT ? OFFSET ?
        `;
        
        db.all(query, [queueType, limit, offset], (err, customers) => {
            if (err) {
                console.error('Error loading queue customers:', err);
                res.status(500).json({ error: 'Database error' });
                return;
            }
            
            // Отправляем сообщение о том, что очередь обработана
            customers.forEach(customer => {
                if (customer.tg_id) {
                    sendTelegramMessage(customer.tg_id, `Уважаемый ${customer.name}, ваше место в очереди ${queueType} обновлено.`);
                }
                if (customer.phone) {
                    sendWhatsAppMessage(customer.phone, `Уважаемый ${customer.name}, ваше место в очереди ${queueType} обновлено.`);
                }
            });

            res.json({
                customers: customers || [],
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

// API для массовой рассылки по очереди
app.post('/api/call-queues/:queueType/broadcast', async (req, res) => {
    const { queueType } = req.params;
    const { message, channels } = req.body; // channels: ['telegram', 'whatsapp']
    
    if (!message || !message.trim()) {
        return res.status(400).json({ error: 'Сообщение не может быть пустым' });
    }
    
    if (!channels || !Array.isArray(channels) || channels.length === 0) {
        return res.status(400).json({ error: 'Выберите хотя бы один канал для рассылки' });
    }
    
    // Получаем клиентов из очереди
    const query = `
        SELECT 
            cq.agent_id,
            cd.name,
            cd.phone,
            u.tg_id
        FROM call_queues cq
        LEFT JOIN contractors_data cd ON cq.agent_id = cd.agent_id
        LEFT JOIN user_map u ON cq.agent_id = u.agent_id
        WHERE cq.queue_type = ? AND cq.is_active = 1
        ORDER BY cq.priority ASC, cq.score DESC
    `;
    
    db.all(query, [queueType], async (err, customers) => {
        if (err) {
            console.error('Error loading queue customers for broadcast:', err);
            return res.status(500).json({ error: 'Database error' });
        }
        
        let telegramSent = 0;
        let whatsappSent = 0;
        let errors = 0;
        
        const results = [];
        
        for (const customer of customers) {
            const customerResult = {
                agent_id: customer.agent_id,
                name: customer.name,
                telegram: null,
                whatsapp: null
            };
            
            // Отправка в Telegram
            if (channels.includes('telegram') && customer.tg_id) {
                try {
                    const success = await sendTelegramMessage(customer.tg_id, message);
                    if (success) {
                        telegramSent++;
                        customerResult.telegram = 'success';
                    } else {
                        errors++;
                        customerResult.telegram = 'error';
                    }
                } catch (error) {
                    errors++;
                    customerResult.telegram = 'error';
                }
            } else if (channels.includes('telegram') && !customer.tg_id) {
                customerResult.telegram = 'no_tg_id';
            }
            
            // Отправка в WhatsApp
            if (channels.includes('whatsapp') && customer.phone) {
                try {
                    const success = await sendWhatsAppMessage(customer.phone, message);
                    if (success) {
                        whatsappSent++;
                        customerResult.whatsapp = 'success';
                    } else {
                        errors++;
                        customerResult.whatsapp = 'error';
                    }
                } catch (error) {
                    errors++;
                    customerResult.whatsapp = 'error';
                }
            } else if (channels.includes('whatsapp') && !customer.phone) {
                customerResult.whatsapp = 'no_phone';
            }
            
            results.push(customerResult);
            
            // Небольшая задержка между отправками для избежания лимитов
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        res.json({
            success: true,
            queue_type: queueType,
            message: message,
            channels: channels,
            stats: {
                total_customers: customers.length,
                telegram_sent: telegramSent,
                whatsapp_sent: whatsappSent,
                errors: errors
            },
            results: results
        });
    });
});

// API для массовой рассылки сообщений по очереди
app.post('/api/messages/bulk', async (req, res) => {
    const { queue_type, message, channel } = req.body;
    
    if (!queue_type || !message || !channel) {
        return res.status(400).json({ error: 'queue_type, message и channel обязательны' });
    }
    
    // Получаем клиентов из очереди
    const query = `
        SELECT 
            cq.agent_id,
            cd.name,
            cd.phone,
            u.tg_id
        FROM call_queues cq
        LEFT JOIN contractors_data cd ON cq.agent_id = cd.agent_id
        LEFT JOIN user_map u ON cq.agent_id = u.agent_id
        WHERE cq.queue_type = ? AND cq.is_active = 1
        ORDER BY cq.priority ASC, cq.score DESC
    `;
    
    db.all(query, [queue_type], async (err, customers) => {
        if (err) {
            console.error('Error loading queue customers for broadcast:', err);
            return res.status(500).json({ error: 'Database error' });
        }
        
        let sent_count = 0;
        let errors = 0;
        
        for (const customer of customers) {
            try {
                let success = false;
                
                if (channel === 'telegram' && customer.tg_id) {
                    success = await sendTelegramMessage(customer.tg_id, message);
                } else if (channel === 'whatsapp' && customer.phone) {
                    success = await sendWhatsAppMessage(customer.phone, message);
                } else if (channel === 'sms' && customer.phone) {
                    success = await sendSMSMessage(customer.phone, message);
                }
                
                if (success) {
                    sent_count++;
                } else {
                    errors++;
                }
            } catch (error) {
                console.error('Error sending message:', error);
                errors++;
            }
            
            // Небольшая задержка между отправками
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        res.json({
            success: true,
            queue_type: queue_type,
            message: message,
            channel: channel,
            sent_count: sent_count,
            errors: errors,
            total_customers: customers.length
        });
    });
});

// API для отправки персонального сообщения
app.post('/api/messages/personal', async (req, res) => {
    const { agent_id, message, channel } = req.body; // channel: 'telegram' or 'whatsapp'
    
    if (!agent_id || !message || !channel) {
        return res.status(400).json({ error: 'agent_id, message и channel обязательны' });
    }
    
    // Получаем данные клиента
    const query = `
        SELECT 
            cd.name,
            cd.phone,
            u.tg_id
        FROM contractors_data cd
        LEFT JOIN user_map u ON cd.agent_id = u.agent_id
        WHERE cd.agent_id = ?
    `;
    
    db.get(query, [agent_id], async (err, customer) => {
        if (err) {
            console.error('Error loading customer for personal message:', err);
            return res.status(500).json({ error: 'Database error' });
        }
        
        if (!customer) {
            return res.status(404).json({ error: 'Клиент не найден' });
        }
        
        let success = false;
        let error_message = null;
        
        try {
            if (channel === 'telegram') {
                if (!customer.tg_id) {
                    return res.status(400).json({ error: 'У клиента нет Telegram ID' });
                }
                success = await sendTelegramMessage(customer.tg_id, message);
            } else if (channel === 'whatsapp') {
                if (!customer.phone) {
                    return res.status(400).json({ error: 'У клиента нет номера телефона' });
                }
                success = await sendWhatsAppMessage(customer.phone, message);
            } else {
                return res.status(400).json({ error: 'Неверный канал. Используйте telegram или whatsapp' });
            }
        } catch (error) {
            error_message = error.message;
        }
        
        res.json({
            success: success,
            agent_id: agent_id,
            customer_name: customer.name,
            channel: channel,
            message: message,
            error: error_message
        });
    });
});

// Пример использования для тестирования
app.post('/api/notify', (req, res) => {
    const { type, chatId, message, phone } = req.body;
    if (type === 'telegram') {
        sendTelegramMessage(chatId, message);
    } else if (type === 'whatsapp') {
        sendWhatsAppMessage(phone, message);
    }
    res.json({ success: true });
});

// Добавление контакта в историю
app.post('/api/call-queues/contact', (req, res) => {
    const { agent_id, contact_type, result, notes } = req.body;
    
    if (!agent_id || !contact_type) {
        res.status(400).json({ error: 'agent_id and contact_type are required' });
        return;
    }
    
    // Сначала находим queue_id для этого agent_id
    db.get('SELECT id FROM call_queues WHERE agent_id = ? AND is_active = 1 LIMIT 1', [agent_id], (err, queue) => {
        if (err || !queue) {
            console.error('Error finding queue:', err);
            res.status(400).json({ error: 'Queue not found for this agent' });
            return;
        }
        
        const query = `
            INSERT INTO contact_history (agent_id, queue_id, contact_type, result, notes)
            VALUES (?, ?, ?, ?, ?)
        `;
        
        db.run(query, [agent_id, queue.id, contact_type, result || 'pending', notes || ''], function(err) {
            if (err) {
                console.error('Error adding contact history:', err);
                res.status(500).json({ error: 'Database error' });
                return;
            }
            
            // Обновляем статус в очереди
            if (result === 'success' || result === 'not_interested') {
                db.run(
                    'UPDATE call_queues SET is_active = 0 WHERE agent_id = ?',
                    [agent_id],
                    (err) => {
                        if (err) console.error('Error updating queue status:', err);
                    }
                );
            }
            
            res.json({
                success: true,
                contactId: this.lastID
            });
        });
    });
});

// Обновление очередей обзвона
app.post('/api/call-queues/refresh', (req, res) => {
    const { spawn } = require('child_process');
    
    // Запускаем SQL скрипт обновления очередей
    const sqlProcess = spawn('sqlite3', [path.join(__dirname, '..', 'loyalty.db')], {
        cwd: __dirname
    });
    
    const sqlScript = require('fs').readFileSync(path.join(__dirname, 'create_call_queues.sql'), 'utf8');
    sqlProcess.stdin.write(sqlScript);
    sqlProcess.stdin.end();
    
    sqlProcess.on('close', (code) => {
        if (code === 0) {
            res.json({ success: true, message: 'Очереди обновлены успешно' });
        } else {
            res.status(500).json({ success: false, message: 'Ошибка обновления очередей' });
        }
    });
    
    sqlProcess.on('error', (error) => {
        console.error('Error refreshing queues:', error);
        res.status(500).json({ success: false, message: 'Ошибка запуска обновления' });
    });
});

// Получение статистики системы
app.get('/api/stats', (req, res) => {
    const queries = {
        totalUsers: 'SELECT COUNT(*) as count FROM bonuses',  // Все контрагенты с бонусами
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

// Получение списка пользователей с пагинацией (ПОКАЗЫВАЕТ ВСЕХ КОНТРАГЕНТОВ С БОНУСАМИ)
app.get('/api/users', (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    const search = req.query.search || '';

    let query = `
        SELECT 
            u.tg_id,
            b.agent_id,
            u.phone,
            u.fullname,
            b.balance,
            l.level_id,
            l.total_spent,
            l.created_at as registered_at,
            CASE WHEN u.agent_id IS NOT NULL THEN 1 ELSE 0 END as is_registered
        FROM bonuses b
        LEFT JOIN user_map u ON b.agent_id = u.agent_id
        LEFT JOIN loyalty_levels l ON b.agent_id = l.agent_id
    `;

    let countQuery = 'SELECT COUNT(*) as total FROM bonuses b';
    let params = [];

    if (search) {
        query += ' WHERE (u.fullname LIKE ? OR u.phone LIKE ? OR b.agent_id LIKE ?)';
        countQuery += ' LEFT JOIN user_map u ON b.agent_id = u.agent_id WHERE (u.fullname LIKE ? OR u.phone LIKE ? OR b.agent_id LIKE ?)';
        const searchParam = `%${search}%`;
        params = [searchParam, searchParam, searchParam];
    }

    query += ' ORDER BY b.balance DESC, l.created_at DESC LIMIT ? OFFSET ?';
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

// Получение детальной информации о клиенте (контрагенте)
app.get('/api/client/:agentId', (req, res) => {
    const { agentId } = req.params;

    // Получаем основную информацию о клиенте
    const clientQuery = `
        SELECT 
            cd.agent_id,
            cd.name,
            cd.description,
            cd.email,
            cd.phone,
            cd.address,
            cd.updated_at,
            b.balance,
            u.tg_id,
            u.fullname as bot_name,
            l.level_id,
            l.total_spent,
            l.created_at as registered_at,
            cs.segment,
            cs.R_score,
            cs.F_score,
            cs.M_score,
            cs.monetary_total,
            cs.frequency,
            cs.recency_days,
            cs.activity_status,
            cs.growth_potential,
            cs.avg_order_value,
            cs.last_purchase_date
        FROM contractors_data cd
        LEFT JOIN bonuses b ON cd.agent_id = b.agent_id
        LEFT JOIN user_map u ON cd.agent_id = u.agent_id
        LEFT JOIN loyalty_levels l ON cd.agent_id = l.agent_id
        LEFT JOIN customer_segments cs ON cd.agent_id = cs.agent_id
        WHERE cd.agent_id = ?
    `;

    db.get(clientQuery, [agentId], (err, client) => {
        if (err) {
            console.error('Database error:', err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        if (!client) {
            res.status(404).json({ error: 'Client not found' });
            return;
        }

        // Получаем отгрузки клиента
        const shipmentsQuery = `
            SELECT 
                demand_id,
                name,
                moment,
                sum,
                state_name,
                positions_count,
                created_at
            FROM contractor_shipments
            WHERE agent_id = ?
            ORDER BY moment DESC
            LIMIT 50
        `;

        db.all(shipmentsQuery, [agentId], (err, shipments) => {
            if (err) {
                console.error('Database error:', err);
                res.status(500).json({ error: 'Database error' });
                return;
            }

            // Получаем транзакции бонусов
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
                    console.error('Database error:', err);
                    res.status(500).json({ error: 'Database error' });
                    return;
                }

                res.json({
                    client: {
                        ...client,
                        balance: client.balance || 0,
                        level_id: client.level_id || 1,
                        total_spent: client.total_spent || 0,
                        is_registered: !!client.tg_id
                    },
                    shipments,
                    transactions
                });
            });
        });
    });
});

// Получение позиций отгрузки
app.get('/api/shipment/:demandId/positions', async (req, res) => {
    const { demandId } = req.params;
    
    try {
        // Получаем данные отгрузки из МойСклад
        const response = await fetch(`${MS_BASE}/entity/demand/${demandId}?expand=positions,positions.assortment,agent,state,attributes`, {
            headers: MS_HEADERS
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Ошибка авторизации МойСклад: токен недействителен или устарел');
            } else if (response.status === 403) {
                throw new Error('Ошибка доступа МойСклад: недостаточно прав для получения данных');
            } else if (response.status === 404) {
                throw new Error('Отгрузка не найдена в МойСклад');
            } else {
                throw new Error(`Ошибка МойСклад API: ${response.status}`);
            }
        }
        
        const demand = await response.json();
        
        // Извлекаем атрибуты автомобиля
        const attributes = demand.attributes || [];
        const carModel = getAttributeValue(attributes, 'Модель Авто') || 
                        getAttributeValue(attributes, 'Марка/модель') || 'Не указано';
        const mileage = getAttributeValue(attributes, 'Пробег') || 'Не указано';
        
        // Обрабатываем позиции
        const positions = demand.positions?.rows?.map((pos, index) => {
            const assortment = pos.assortment || {};
            return {
                id: pos.id || `pos_${index}`,
                assortment_name: assortment.name || 'Не указано',
                quantity: pos.quantity || 0,
                price: pos.price || 0,
                sum: (pos.price || 0) * (pos.quantity || 0),
                vat: pos.vat || 0,
                article: assortment.article || '',
                brand: getAssortmentAttribute(assortment, 'Бренд') || '',
                car_model: carModel,
                mileage: mileage,
                type: assortment.meta?.type || 'product'
            };
        }) || [];
        
        res.json({
            success: true,
            demandId: demandId,
            positions: positions,
            total: positions.reduce((sum, pos) => sum + pos.sum, 0),
            count: positions.length,
            car_info: {
                model: carModel,
                mileage: mileage
            }
        });
        
    } catch (error) {
        console.error('Error fetching shipment positions:', error);
        res.status(500).json({ 
            error: 'Failed to fetch shipment positions',
            message: error.message
        });
    }
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

// API для сегментации клиентов
app.get('/api/customer-segments', (req, res) => {
    const query = `
        SELECT 
            agent_id,
            customer_name,
            phone,
            email,
            bonus_balance,
            loyalty_level,
            is_registered,
            recency_days,
            frequency,
            monetary_total,
            R_score,
            F_score,
            M_score,
            RFM_code,
            segment,
            avg_order_value,
            clv_estimate,
            purchase_frequency_monthly,
            activity_status,
            growth_potential,
            first_purchase_date,
            last_purchase_date,
            purchase_days_count
        FROM customer_segments
        ORDER BY monetary_total DESC
    `;

    db.all(query, [], (err, customers) => {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        // Статистика по сегментам
        const segmentStats = {};
        const activityStats = {};
        let totalRevenue = 0;
        let activeCustomers = 0;

        customers.forEach(customer => {
            const segment = customer.segment;
            const activity = customer.activity_status;
            
            // Статистика по сегментам
            if (!segmentStats[segment]) {
                segmentStats[segment] = {
                    customers_count: 0,
                    total_revenue: 0,
                    avg_revenue: 0,
                    avg_frequency: 0,
                    avg_recency: 0,
                    percentage: 0
                };
            }
            
            segmentStats[segment].customers_count++;
            segmentStats[segment].total_revenue += customer.monetary_total;
            segmentStats[segment].avg_frequency += customer.frequency;
            segmentStats[segment].avg_recency += customer.recency_days;
            
            // Статистика по активности
            activityStats[activity] = (activityStats[activity] || 0) + 1;
            
            totalRevenue += customer.monetary_total;
            if (customer.frequency > 0) activeCustomers++;
        });

        // Рассчитываем средние значения для сегментов
        Object.keys(segmentStats).forEach(segment => {
            const count = segmentStats[segment].customers_count;
            segmentStats[segment].avg_revenue = segmentStats[segment].total_revenue / count;
            segmentStats[segment].avg_frequency = segmentStats[segment].avg_frequency / count;
            segmentStats[segment].avg_recency = segmentStats[segment].avg_recency / count;
            segmentStats[segment].percentage = (count / customers.length * 100).toFixed(1);
        });

        const avgOrderValue = activeCustomers > 0 ? totalRevenue / activeCustomers : 0;

        res.json({
            customers,
            segments: segmentStats,
            activity: activityStats,
            stats: {
                total_customers: customers.length,
                active_customers: activeCustomers,
                total_revenue: totalRevenue,
                avg_order_value: avgOrderValue
            }
        });
    });
});

// Обновление сегментации
app.post('/api/refresh-segmentation', (req, res) => {
    const { spawn } = require('child_process');
    const pythonProcess = spawn('python3', ['customer_segmentation.py'], {
        cwd: path.join(__dirname, '..')
    });

    pythonProcess.on('close', (code) => {
        if (code === 0) {
            res.json({ success: true, message: 'Сегментация обновлена успешно' });
        } else {
            res.status(500).json({ success: false, message: 'Ошибка обновления сегментации' });
        }
    });

    pythonProcess.on('error', (error) => {
        console.error('Error running segmentation:', error);
        res.status(500).json({ success: false, message: 'Ошибка запуска сегментации' });
    });
});

// Прогнозирование клиентов
app.get('/api/analytics/customers-forecast', (req, res) => {
    try {
        const months = parseInt(req.query.months) || 3; // Прогноз на 3 месяца по умолчанию
        
        // Получаем исторические данные за последние 12 месяцев
        const historicalQuery = `
            WITH monthly_data AS (
                SELECT 
                    strftime('%Y-%m', moment) as month,
                    COUNT(DISTINCT CASE 
                        WHEN agent_id NOT IN (
                            SELECT DISTINCT agent_id 
                            FROM contractor_shipments cs2 
                            WHERE strftime('%Y-%m', cs2.moment) < strftime('%Y-%m', cs.moment)
                        ) THEN agent_id 
                    END) as new_customers,
                    COUNT(DISTINCT CASE 
                        WHEN agent_id IN (
                            SELECT DISTINCT agent_id 
                            FROM contractor_shipments cs2 
                            WHERE strftime('%Y-%m', cs2.moment) < strftime('%Y-%m', cs.moment)
                        ) THEN agent_id 
                    END) as existing_customers,
                    ROUND(SUM(CASE 
                        WHEN agent_id NOT IN (
                            SELECT DISTINCT agent_id 
                            FROM contractor_shipments cs2 
                            WHERE strftime('%Y-%m', cs2.moment) < strftime('%Y-%m', cs.moment)
                        ) THEN sum 
                        ELSE 0 
                    END) / 100.0) as new_customers_revenue,
                    ROUND(SUM(CASE 
                        WHEN agent_id IN (
                            SELECT DISTINCT agent_id 
                            FROM contractor_shipments cs2 
                            WHERE strftime('%Y-%m', cs2.moment) < strftime('%Y-%m', cs.moment)
                        ) THEN sum 
                        ELSE 0 
                    END) / 100.0) as existing_customers_revenue,
                    COUNT(*) as total_purchases,
                    ROUND(SUM(sum) / 100.0) as total_revenue
                FROM contractor_shipments cs
                WHERE moment >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', moment)
                ORDER BY month ASC
            )
            SELECT * FROM monthly_data;
        `;
        
        db.all(historicalQuery, [], (err, historicalData) => {
            if (err) {
                console.error('Database error:', err);
                return res.status(500).json({ error: 'Ошибка базы данных' });
            }
            
            if (historicalData.length < 3) {
                return res.json({
                    error: 'Недостаточно данных для прогнозирования (минимум 3 месяца)',
                    forecast: [],
                    historical_data: historicalData
                });
            }
            
            // Вычисляем прогноз
            const forecast = calculateForecast(historicalData, months);
            
            res.json({
                historical_data: historicalData,
                forecast: forecast,
                forecast_months: months,
                algorithm: 'Линейная регрессия с сезонностью',
                generated_at: new Date().toISOString()
            });
        });
        
    } catch (error) {
        console.error('Ошибка получения прогноза:', error);
        res.status(500).json({ error: 'Ошибка получения прогноза' });
    }
});

// Функция для вычисления прогноза
function calculateForecast(historicalData, months) {
    const forecast = [];
    
    // Извлекаем временные ряды
    const newCustomersData = historicalData.map(d => d.new_customers || 0);
    const existingCustomersData = historicalData.map(d => d.existing_customers || 0);
    const newRevenueData = historicalData.map(d => d.new_customers_revenue || 0);
    const existingRevenueData = historicalData.map(d => d.existing_customers_revenue || 0);
    const totalPurchasesData = historicalData.map(d => d.total_purchases || 0);
    
    // Вычисляем тренды (простая линейная регрессия)
    const newCustomersTrend = calculateLinearTrend(newCustomersData);
    const existingCustomersTrend = calculateLinearTrend(existingCustomersData);
    const newRevenueTrend = calculateLinearTrend(newRevenueData);
    const existingRevenueTrend = calculateLinearTrend(existingRevenueData);
    const purchasesTrend = calculateLinearTrend(totalPurchasesData);
    
    // Вычисляем сезонность (среднее по месяцам)
    const seasonality = calculateSeasonality(historicalData);
    
    // Генерируем прогноз
    const lastDate = new Date(historicalData[historicalData.length - 1].month + '-01');
    
    for (let i = 1; i <= months; i++) {
        const forecastDate = new Date(lastDate);
        forecastDate.setMonth(forecastDate.getMonth() + i);
        const forecastMonth = forecastDate.toISOString().substr(0, 7);
        const monthIndex = forecastDate.getMonth(); // 0-11
        
        // Базовый прогноз на основе тренда
        const baseNewCustomers = Math.max(0, Math.round(
            newCustomersTrend.slope * (historicalData.length + i) + newCustomersTrend.intercept
        ));
        const baseExistingCustomers = Math.max(0, Math.round(
            existingCustomersTrend.slope * (historicalData.length + i) + existingCustomersTrend.intercept
        ));
        const baseNewRevenue = Math.max(0, Math.round(
            newRevenueTrend.slope * (historicalData.length + i) + newRevenueTrend.intercept
        ));
        const baseExistingRevenue = Math.max(0, Math.round(
            existingRevenueTrend.slope * (historicalData.length + i) + existingRevenueTrend.intercept
        ));
        const basePurchases = Math.max(0, Math.round(
            purchasesTrend.slope * (historicalData.length + i) + purchasesTrend.intercept
        ));
        
        // Применяем сезонную корректировку
        const seasonalFactor = seasonality[monthIndex] || 1;
        
        const forecastData = {
            month: forecastMonth,
            new_customers: Math.round(baseNewCustomers * seasonalFactor),
            existing_customers: Math.round(baseExistingCustomers * seasonalFactor),
            new_customers_revenue: Math.round(baseNewRevenue * seasonalFactor),
            existing_customers_revenue: Math.round(baseExistingRevenue * seasonalFactor),
            total_purchases: Math.round(basePurchases * seasonalFactor),
            total_revenue: Math.round((baseNewRevenue + baseExistingRevenue) * seasonalFactor),
            total_customers: Math.round((baseNewCustomers + baseExistingCustomers) * seasonalFactor),
            confidence: Math.max(0.3, Math.min(0.9, 0.9 - (i - 1) * 0.15)), // Уверенность снижается с временем
            type: 'forecast'
        };
        
        forecast.push(forecastData);
    }
    
    return forecast;
}

// Вычисление линейного тренда
function calculateLinearTrend(data) {
    const n = data.length;
    const sumX = (n * (n + 1)) / 2;
    const sumY = data.reduce((sum, y) => sum + y, 0);
    const sumXY = data.reduce((sum, y, i) => sum + (i + 1) * y, 0);
    const sumX2 = (n * (n + 1) * (2 * n + 1)) / 6;
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    return { slope, intercept };
}

// Вычисление сезонности
function calculateSeasonality(historicalData) {
    const monthlyAverages = {};
    const monthlyTotals = {};
    const monthlyCounts = {};
    
    historicalData.forEach(data => {
        const date = new Date(data.month + '-01');
        const monthIndex = date.getMonth();
        
        if (!monthlyTotals[monthIndex]) {
            monthlyTotals[monthIndex] = 0;
            monthlyCounts[monthIndex] = 0;
        }
        
        monthlyTotals[monthIndex] += data.total_revenue || 0;
        monthlyCounts[monthIndex]++;
    });
    
    // Вычисляем средние значения по месяцам
    Object.keys(monthlyTotals).forEach(month => {
        monthlyAverages[month] = monthlyTotals[month] / monthlyCounts[month];
    });
    
    // Вычисляем общее среднее
    const overallAverage = Object.values(monthlyAverages).reduce((sum, avg) => sum + avg, 0) / Object.values(monthlyAverages).length;
    
    // Вычисляем сезонные коэффициенты
    const seasonality = {};
    Object.keys(monthlyAverages).forEach(month => {
        seasonality[month] = monthlyAverages[month] / overallAverage;
    });
    
    return seasonality;
}

// API для получения аналитики клиентов по месяцам
app.get('/api/analytics/customers-monthly', (req, res) => {
    const months = parseInt(req.query.months) || 12;
    
    const query = `
        WITH monthly_data AS (
            SELECT 
                strftime('%Y-%m', cs.moment) as month,
                cs.agent_id,
                MIN(cs.moment) as first_purchase_month,
                COUNT(*) as purchases_count,
                SUM(cs.sum) as total_amount
            FROM contractor_shipments cs
            WHERE cs.moment IS NOT NULL 
                AND cs.moment >= datetime('now', '-' || ? || ' months')
            GROUP BY strftime('%Y-%m', cs.moment), cs.agent_id
        ),
        customer_types AS (
            SELECT 
                md.month,
                md.agent_id,
                md.purchases_count,
                md.total_amount,
                -- Определяем тип клиента: новый или существующий
                CASE 
                    WHEN md.first_purchase_month = md.month THEN 'new'
                    ELSE 'existing'
                END as customer_type,
                -- Проверяем, были ли отгрузки до этого месяца
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM contractor_shipments cs_prev 
                        WHERE cs_prev.agent_id = md.agent_id 
                        AND strftime('%Y-%m', cs_prev.moment) < md.month
                    ) THEN 'existing'
                    ELSE 'new'
                END as customer_type_corrected
            FROM monthly_data md
        )
        SELECT 
            ct.month,
            ct.customer_type_corrected as customer_type,
            COUNT(DISTINCT ct.agent_id) as customers_count,
            SUM(ct.total_amount) as total_revenue,
            AVG(ct.total_amount) as avg_revenue_per_customer,
            SUM(ct.purchases_count) as total_purchases
        FROM customer_types ct
        GROUP BY ct.month, ct.customer_type_corrected
        ORDER BY ct.month DESC, ct.customer_type_corrected
    `;
    
    db.all(query, [months], (err, results) => {
        if (err) {
            console.error('Error fetching customer analytics:', err);
            res.status(500).json({ error: 'Database error' });
            return;
        }
        
        // Группируем данные по месяцам
        const monthlyStats = {};
        const monthlyTotals = {};
        
        results.forEach(row => {
            const month = row.month;
            
            if (!monthlyStats[month]) {
                monthlyStats[month] = {
                    month: month,
                    new_customers: 0,
                    existing_customers: 0,
                    new_customers_revenue: 0,
                    existing_customers_revenue: 0,
                    new_customers_purchases: 0,
                    existing_customers_purchases: 0
                };
            }
            
            if (row.customer_type === 'new') {
                monthlyStats[month].new_customers = row.customers_count;
                monthlyStats[month].new_customers_revenue = row.total_revenue;
                monthlyStats[month].new_customers_purchases = row.total_purchases;
            } else {
                monthlyStats[month].existing_customers = row.customers_count;
                monthlyStats[month].existing_customers_revenue = row.total_revenue;
                monthlyStats[month].existing_customers_purchases = row.total_purchases;
            }
            
            // Подсчитываем общие итоги по месяцам
            if (!monthlyTotals[month]) {
                monthlyTotals[month] = {
                    month: month,
                    total_customers: 0,
                    total_revenue: 0,
                    total_purchases: 0
                };
            }
            
            monthlyTotals[month].total_customers += row.customers_count;
            monthlyTotals[month].total_revenue += row.total_revenue;
            monthlyTotals[month].total_purchases += row.total_purchases;
        });
        
        // Конвертируем в массивы и сортируем, переводим выручку из копеек в рубли
        const monthlyData = Object.values(monthlyStats).map(item => ({
            ...item,
            new_customers_revenue: Math.round(item.new_customers_revenue / 100),
            existing_customers_revenue: Math.round(item.existing_customers_revenue / 100)
        })).sort((a, b) => b.month.localeCompare(a.month));
        
        const totalsData = Object.values(monthlyTotals).map(item => ({
            ...item,
            total_revenue: Math.round(item.total_revenue / 100)
        })).sort((a, b) => b.month.localeCompare(a.month));
        
        res.json({
            monthly_analytics: monthlyData,
            monthly_totals: totalsData,
            period: `${months} месяцев`,
            generated_at: new Date().toISOString()
        });
    });
});

// Новый эндпоинт для получения всех контрагентов из МойСклад
app.get('/api/all-contractors', (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;
    const search = req.query.search || '';

    let query = `
        SELECT 
            c.agent_id,
            c.name as fullname,
            c.phone,
            c.email,
            c.address,
            COALESCE(b.balance, 0) as balance,
            COALESCE(l.level_id, 1) as level_id,
            COALESCE(l.total_spent, 0) as total_spent,
            u.tg_id,
            l.created_at as registered_at,
            CASE WHEN u.agent_id IS NOT NULL THEN 1 ELSE 0 END as is_registered
        FROM contractors_data c
        LEFT JOIN bonuses b ON c.agent_id = b.agent_id
        LEFT JOIN user_map u ON c.agent_id = u.agent_id
        LEFT JOIN loyalty_levels l ON c.agent_id = l.agent_id
    `;

    let countQuery = 'SELECT COUNT(*) as total FROM contractors_data c';
    let params = [];

    if (search) {
        query += ' WHERE (c.name LIKE ? OR c.phone LIKE ? OR c.agent_id LIKE ?)';
        countQuery += ' WHERE (c.name LIKE ? OR c.phone LIKE ? OR c.agent_id LIKE ?)';
        const searchParam = `%${search}%`;
        params = [searchParam, searchParam, searchParam];
    }

    query += ' ORDER BY COALESCE(b.balance, 0) DESC, c.name ASC LIMIT ? OFFSET ?';
    params.push(limit, offset);

    // Получаем общее количество записей
    db.get(countQuery, search ? [params[0], params[1], params[2]] : [], (err, countRow) => {
        if (err) {
            console.error(err);
            res.status(500).json({ error: 'Database error' });
            return;
        }

        // Получаем контрагентов
        db.all(query, params, (err, contractors) => {
            if (err) {
                console.error(err);
                res.status(500).json({ error: 'Database error' });
                return;
            }

            res.json({
                contractors: contractors.map(contractor => ({
                    ...contractor,
                    balance: contractor.balance || 0,
                    level_id: contractor.level_id || 1,
                    total_spent: contractor.total_spent || 0,
                    fullname: contractor.fullname || 'Без названия',
                    phone: contractor.phone || 'Не указан',
                    email: contractor.email || 'Не указан',
                    tg_id: contractor.tg_id || null
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
