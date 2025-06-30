/**
 * Модуль для работы с базой данных PostgreSQL в веб-приложении.
 * Заменяет функциональность исходного api_integration.js.
 */
require('dotenv').config();
const { Pool } = require('pg');
const logger = require('./logger');

// Проверка настроек подключения
const requiredEnvVars = [
  'POSTGRES_HOST',
  'POSTGRES_PORT',
  'POSTGRES_USER',
  'POSTGRES_PASSWORD',
  'POSTGRES_DB'
];

const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
if (missingVars.length > 0) {
  throw new Error(`Отсутствуют необходимые переменные окружения: ${missingVars.join(', ')}`);
}

// Настройка пула соединений PostgreSQL
const pool = new Pool({
  host: process.env.POSTGRES_HOST,
  port: process.env.POSTGRES_PORT,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB,
  max: 20, // максимальное количество соединений в пуле
  idleTimeoutMillis: 30000, // время простоя соединения до закрытия
  connectionTimeoutMillis: 2000, // время ожидания подключения
  ssl: {
    rejectUnauthorized: false // Для подключения к Render PostgreSQL
  }
});

// Проверка соединения при инициализации
pool.query('SELECT NOW()')
  .then(() => {
    logger.info(`Успешное подключение к PostgreSQL (${process.env.POSTGRES_HOST}:${process.env.POSTGRES_PORT}/${process.env.POSTGRES_DB})`);
  })
  .catch(err => {
    logger.error(`Ошибка подключения к PostgreSQL: ${err.message}`);
    throw err;
  });

/**
 * Получает ID агента по ID пользователя Telegram
 * @param {number} tgId - ID пользователя Telegram
 * @returns {Promise<string|null>} - ID агента (контрагента) или null, если не найден
 */
async function getAgentId(tgId) {
  try {
    const result = await pool.query('SELECT agent_id FROM user_map WHERE tg_id = $1', [tgId]);
    return result.rows.length > 0 ? result.rows[0].agent_id : null;
  } catch (error) {
    logger.error(`[getAgentId] Ошибка получения agent_id: ${error.message}`);
    return null;
  }
}

/**
 * Получает пользователя по номеру телефона
 * @param {string} phone - Номер телефона
 * @returns {Promise<object|null>} - Объект пользователя или null, если не найден
 */
async function getUserByPhone(phone) {
  try {
    const result = await pool.query(
      'SELECT tg_id, agent_id, phone, fullname FROM user_map WHERE phone = $1',
      [phone]
    );
    return result.rows.length > 0 ? result.rows[0] : null;
  } catch (error) {
    logger.error(`[getUserByPhone] Ошибка получения пользователя: ${error.message}`);
    return null;
  }
}

/**
 * Получает пользователя по ID в Telegram
 * @param {number} tgId - ID пользователя Telegram
 * @returns {Promise<object|null>} - Объект пользователя или null, если не найден
 */
async function getUserByTgId(tgId) {
  try {
    const result = await pool.query(
      'SELECT tg_id, agent_id, phone, fullname FROM user_map WHERE tg_id = $1',
      [tgId]
    );
    return result.rows.length > 0 ? result.rows[0] : null;
  } catch (error) {
    logger.error(`[getUserByTgId] Ошибка получения пользователя: ${error.message}`);
    return null;
  }
}

/**
 * Регистрирует связь между пользователем Telegram и агентом
 * @param {number} tgId - ID пользователя Telegram
 * @param {string} agentId - ID агента (контрагента)
 * @param {string} phone - Номер телефона
 * @param {string} fullname - Полное имя пользователя
 * @returns {Promise<boolean>} - true, если операция успешна
 */
async function registerMapping(tgId, agentId, phone, fullname) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // Добавление или обновление пользователя
    await client.query(`
      INSERT INTO user_map(tg_id, agent_id, phone, fullname)
      VALUES ($1, $2, $3, $4)
      ON CONFLICT(tg_id) DO UPDATE
      SET agent_id = EXCLUDED.agent_id,
          phone = EXCLUDED.phone,
          fullname = EXCLUDED.fullname
    `, [tgId, agentId, phone, fullname]);

    // Создание записи баланса, если она не существует
    await client.query(`
      INSERT INTO bonuses(agent_id, balance) VALUES($1, $2)
      ON CONFLICT(agent_id) DO NOTHING
    `, [agentId, 10000]); // 100 бонусов для нового пользователя

    // Инициализация уровня лояльности
    await client.query(`
      INSERT INTO loyalty_levels(agent_id, level_id, total_spent)
      VALUES ($1, 1, 0)
      ON CONFLICT(agent_id) DO NOTHING
    `, [agentId]);

    await client.query('COMMIT');
    logger.info(`Регистрация пользователя: tg_id=${tgId}, agent_id=${agentId}`);
    return true;
  } catch (error) {
    await client.query('ROLLBACK');
    logger.error(`[registerMapping] Ошибка регистрации пользователя: ${error.message}`);
    return false;
  } finally {
    client.release();
  }
}

/**
 * Получает текущий баланс бонусов
 * @param {string} agentId - ID агента (контрагента)
 * @returns {Promise<number>} - Текущий баланс бонусов
 */
async function getBalance(agentId) {
  try {
    const result = await pool.query('SELECT balance FROM bonuses WHERE agent_id = $1', [agentId]);
    return result.rows.length > 0 ? parseInt(result.rows[0].balance) : 0;
  } catch (error) {
    logger.error(`[getBalance] Ошибка получения баланса: ${error.message}`);
    return 0;
  }
}

/**
 * Изменяет баланс бонусов на указанную величину
 * @param {string} agentId - ID агента (контрагента)
 * @param {number} delta - Величина изменения баланса
 * @returns {Promise<boolean>} - true, если операция успешна
 */
async function changeBalance(agentId, delta) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    
    await client.query(`
      INSERT INTO bonuses(agent_id, balance) VALUES($1, $2)
      ON CONFLICT(agent_id) DO UPDATE SET balance = bonuses.balance + $2
    `, [agentId, delta]);
    
    await client.query('COMMIT');
    logger.info(`Изменение баланса: agent_id=${agentId}, delta=${delta}`);
    return true;
  } catch (error) {
    await client.query('ROLLBACK');
    logger.error(`[changeBalance] Ошибка изменения баланса: ${error.message}`);
    return false;
  } finally {
    client.release();
  }
}

/**
 * Получает информацию об уровне лояльности клиента
 * @param {string} agentId - ID агента (контрагента)
 * @returns {Promise<object>} - Объект с информацией об уровне лояльности
 */
async function getLoyaltyLevel(agentId) {
  try {
    const result = await pool.query(`
      SELECT level_id, total_spent, total_earned, total_redeemed
      FROM loyalty_levels WHERE agent_id = $1
    `, [agentId]);
    
    if (result.rows.length === 0) {
      // Инициализация уровня лояльности, если не существует
      await pool.query(`
        INSERT INTO loyalty_levels(agent_id, level_id, total_spent)
        VALUES ($1, 1, 0)
        ON CONFLICT(agent_id) DO NOTHING
      `, [agentId]);
      
      return {
        level_id: 1,
        total_spent: 0,
        total_earned: 0,
        total_redeemed: 0
      };
    }
    
    return {
      level_id: parseInt(result.rows[0].level_id),
      total_spent: parseInt(result.rows[0].total_spent),
      total_earned: parseInt(result.rows[0].total_earned || 0),
      total_redeemed: parseInt(result.rows[0].total_redeemed || 0)
    };
  } catch (error) {
    logger.error(`[getLoyaltyLevel] Ошибка получения уровня лояльности: ${error.message}`);
    return {
      level_id: 1,
      total_spent: 0,
      total_earned: 0,
      total_redeemed: 0
    };
  }
}

/**
 * Получает историю транзакций бонусов за указанный период
 * @param {string} agentId - ID агента (контрагента)
 * @param {number} days - Количество дней для отображения истории
 * @returns {Promise<Array>} - Массив транзакций
 */
async function getBonusTransactions(agentId, days = 30) {
  try {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    const result = await pool.query(`
      SELECT transaction_type, amount, description, related_demand_id, created_at
      FROM bonus_transactions
      WHERE agent_id = $1 AND created_at >= $2
      ORDER BY created_at DESC
    `, [agentId, cutoffDate.toISOString()]);
    
    return result.rows.map(row => ({
      type: row.transaction_type,
      amount: parseInt(row.amount),
      description: row.description,
      related_demand_id: row.related_demand_id,
      date: row.created_at
    }));
  } catch (error) {
    logger.error(`[getBonusTransactions] Ошибка получения истории транзакций: ${error.message}`);
    return [];
  }
}

/**
 * Добавляет запись о транзакции бонусов
 * @param {string} agentId - ID агента (контрагента)
 * @param {string} transactionType - Тип транзакции ('accrual' или 'redemption')
 * @param {number} amount - Сумма транзакции
 * @param {string} description - Описание транзакции
 * @param {string} relatedDemandId - ID связанного заказа (опционально)
 * @returns {Promise<boolean>} - true, если операция успешна
 */
async function addBonusTransaction(agentId, transactionType, amount, description, relatedDemandId = null) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    
    // Добавление транзакции
    await client.query(`
      INSERT INTO bonus_transactions 
      (agent_id, transaction_type, amount, description, related_demand_id)
      VALUES ($1, $2, $3, $4, $5)
    `, [agentId, transactionType, amount, description, relatedDemandId]);
    
    // Обновление счетчика в таблице loyalty_levels
    if (transactionType === 'accrual') {
      await client.query(`
        UPDATE loyalty_levels SET total_earned = total_earned + $1
        WHERE agent_id = $2
      `, [amount, agentId]);
    } else if (transactionType === 'redemption') {
      await client.query(`
        UPDATE loyalty_levels SET total_redeemed = total_redeemed + $1
        WHERE agent_id = $2
      `, [Math.abs(amount), agentId]);
    }
    
    await client.query('COMMIT');
    logger.info(`Транзакция бонусов: agent_id=${agentId}, type=${transactionType}, amount=${amount}`);
    return true;
  } catch (error) {
    await client.query('ROLLBACK');
    logger.error(`[addBonusTransaction] Ошибка добавления транзакции: ${error.message}`);
    return false;
  } finally {
    client.release();
  }
}

/**
 * Получает историю технического обслуживания
 * @param {string} agentId - ID агента (контрагента)
 * @returns {Promise<Array>} - Массив записей о техническом обслуживании
 */
async function getMaintenanceHistory(agentId) {
  try {
    const result = await pool.query(`
      SELECT id, work_id, performed_date, mileage, source, demand_id, notes, created_at
      FROM maintenance_history
      WHERE agent_id = $1
      ORDER BY performed_date DESC
    `, [agentId]);
    
    return result.rows.map(row => ({
      id: row.id,
      work_id: row.work_id,
      performed_date: row.performed_date,
      mileage: row.mileage,
      source: row.source,
      demand_id: row.demand_id,
      notes: row.notes,
      created_at: row.created_at
    }));
  } catch (error) {
    logger.error(`[getMaintenanceHistory] Ошибка получения истории ТО: ${error.message}`);
    return [];
  }
}

/**
 * Добавляет запись о техническом обслуживании
 * @param {string} agentId - ID агента (контрагента)
 * @param {object} maintenanceData - Данные о техническом обслуживании
 * @returns {Promise<boolean>} - true, если операция успешна
 */
async function addMaintenanceRecord(agentId, maintenanceData) {
  try {
    await pool.query(`
      INSERT INTO maintenance_history
      (agent_id, work_id, performed_date, mileage, source, demand_id, notes)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
    `, [
      agentId,
      maintenanceData.work_id,
      maintenanceData.performed_date,
      maintenanceData.mileage,
      maintenanceData.source || 'manual',
      maintenanceData.demand_id,
      maintenanceData.notes
    ]);
    
    logger.info(`Добавлена запись ТО: agent_id=${agentId}, work_id=${maintenanceData.work_id}`);
    return true;
  } catch (error) {
    logger.error(`[addMaintenanceRecord] Ошибка добавления записи ТО: ${error.message}`);
    return false;
  }
}

/**
 * Получает настройки технического обслуживания для пользователя
 * @param {string} agentId - ID агента (контрагента)
 * @returns {Promise<Array>} - Массив настроек ТО
 */
async function getMaintenanceSettings(agentId) {
  try {
    const result = await pool.query(`
      SELECT work_id, custom_mileage_interval, custom_time_interval, is_active
      FROM maintenance_settings
      WHERE agent_id = $1
    `, [agentId]);
    
    return result.rows.map(row => ({
      work_id: row.work_id,
      custom_mileage_interval: row.custom_mileage_interval,
      custom_time_interval: row.custom_time_interval,
      is_active: row.is_active
    }));
  } catch (error) {
    logger.error(`[getMaintenanceSettings] Ошибка получения настроек ТО: ${error.message}`);
    return [];
  }
}

/**
 * Обновляет настройки технического обслуживания для пользователя
 * @param {string} agentId - ID агента (контрагента)
 * @param {number} workId - ID работы
 * @param {object} settings - Новые настройки
 * @returns {Promise<boolean>} - true, если операция успешна
 */
async function updateMaintenanceSetting(agentId, workId, settings) {
  try {
    await pool.query(`
      INSERT INTO maintenance_settings
      (agent_id, work_id, custom_mileage_interval, custom_time_interval, is_active)
      VALUES ($1, $2, $3, $4, $5)
      ON CONFLICT(agent_id, work_id) DO UPDATE
      SET custom_mileage_interval = EXCLUDED.custom_mileage_interval,
          custom_time_interval = EXCLUDED.custom_time_interval,
          is_active = EXCLUDED.is_active
    `, [
      agentId,
      workId,
      settings.custom_mileage_interval,
      settings.custom_time_interval,
      settings.is_active !== undefined ? settings.is_active : true
    ]);
    
    logger.info(`Обновлены настройки ТО: agent_id=${agentId}, work_id=${workId}`);
    return true;
  } catch (error) {
    logger.error(`[updateMaintenanceSetting] Ошибка обновления настроек ТО: ${error.message}`);
    return false;
  }
}

// Экспорт функций для использования в других модулях
module.exports = {
  getAgentId,
  getUserByPhone,
  getUserByTgId,
  registerMapping,
  getBalance,
  changeBalance,
  getLoyaltyLevel,
  getBonusTransactions,
  addBonusTransaction,
  getMaintenanceHistory,
  addMaintenanceRecord,
  getMaintenanceSettings,
  updateMaintenanceSetting
};
