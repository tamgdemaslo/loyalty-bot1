// Простой тест для проверки работы админ панели
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Путь к базе данных
const dbPath = path.join(__dirname, 'loyalty.db');

console.log('🔍 Проверка админ панели...');

// Проверяем наличие базы данных
const fs = require('fs');
if (!fs.existsSync(dbPath)) {
    console.log('❌ База данных не найдена по пути:', dbPath);
    console.log('📝 Создание тестовой базы данных...');
    
    // Создаем тестовую базу
    const db = new sqlite3.Database(dbPath);
    
    db.serialize(() => {
        // Создаем таблицы
        db.run(`
            CREATE TABLE IF NOT EXISTS user_map (
                tg_id    INTEGER PRIMARY KEY,
                agent_id TEXT    NOT NULL,
                phone    TEXT    DEFAULT '',
                fullname TEXT    DEFAULT ''
            )
        `);
        
        db.run(`
            CREATE TABLE IF NOT EXISTS bonuses (
                agent_id TEXT PRIMARY KEY,
                balance  INTEGER NOT NULL DEFAULT 0
            )
        `);
        
        db.run(`
            CREATE TABLE IF NOT EXISTS loyalty_levels (
                agent_id TEXT PRIMARY KEY,
                level_id INTEGER NOT NULL DEFAULT 1,
                total_spent INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        db.run(`
            CREATE TABLE IF NOT EXISTS bonus_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT NOT NULL,
                related_demand_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        // Добавляем тестовые данные
        console.log('📊 Добавление тестовых данных...');
        
        // Тестовые пользователи
        const testUsers = [
            { tg_id: 12345, agent_id: 'test_001', phone: '+7 999 123-45-67', fullname: 'Иван Петров' },
            { tg_id: 12346, agent_id: 'test_002', phone: '+7 999 123-45-68', fullname: 'Мария Сидорова' },
            { tg_id: 12347, agent_id: 'test_003', phone: '+7 999 123-45-69', fullname: 'Алексей Иванов' }
        ];
        
        testUsers.forEach(user => {
            db.run(`
                INSERT OR REPLACE INTO user_map (tg_id, agent_id, phone, fullname)
                VALUES (?, ?, ?, ?)
            `, [user.tg_id, user.agent_id, user.phone, user.fullname]);
            
            db.run(`
                INSERT OR REPLACE INTO bonuses (agent_id, balance)
                VALUES (?, ?)
            `, [user.agent_id, Math.floor(Math.random() * 5000) + 1000]);
            
            db.run(`
                INSERT OR REPLACE INTO loyalty_levels (agent_id, level_id, total_spent)
                VALUES (?, ?, ?)
            `, [user.agent_id, Math.floor(Math.random() * 5) + 1, Math.floor(Math.random() * 50000)]);
        });
        
        // Тестовые транзакции
        const transactions = [
            { agent_id: 'test_001', type: 'accrual', amount: 500, description: 'Тестовое начисление' },
            { agent_id: 'test_002', type: 'redemption', amount: 200, description: 'Тестовое списание' },
            { agent_id: 'test_003', type: 'accrual', amount: 750, description: 'Бонус за визит' }
        ];
        
        transactions.forEach(trans => {
            db.run(`
                INSERT INTO bonus_transactions (agent_id, transaction_type, amount, description)
                VALUES (?, ?, ?, ?)
            `, [trans.agent_id, trans.type, trans.amount, trans.description]);
        });
        
        console.log('✅ Тестовые данные добавлены');
    });
    
    db.close();
} else {
    console.log('✅ База данных найдена:', dbPath);
}

// Проверяем API
async function testAPI() {
    try {
        console.log('🚀 Запуск тестового сервера...');
        
        // Запускаем админ сервер для теста
        const adminServer = require('./admin/server.js');
        
        // Даем время серверу запуститься
        setTimeout(async () => {
            try {
                console.log('🔗 Тестирование API...');
                
                // Тест статистики
                const statsResponse = await fetch('http://localhost:3001/api/stats');
                if (statsResponse.ok) {
                    const stats = await statsResponse.json();
                    console.log('📊 Статистика:', stats);
                    console.log('✅ API работает корректно!');
                } else {
                    console.log('❌ Ошибка API');
                }
                
            } catch (error) {
                console.log('❌ Ошибка тестирования:', error.message);
            }
            
            process.exit(0);
        }, 2000);
        
    } catch (error) {
        console.log('❌ Ошибка запуска:', error.message);
        process.exit(1);
    }
}

// Запускаем тест только если база данных существует
if (fs.existsSync(dbPath)) {
    testAPI();
} else {
    console.log('⚠️  Запустите тест еще раз после создания базы данных');
}
