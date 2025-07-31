require('dotenv').config();
const axios = require('axios');

const API_BASE = 'http://localhost:3001/api';

// Ваши данные
const YOUR_AGENT_ID = '51184984-4f52-11f0-0a80-191f00608b92';
const YOUR_TG_ID = '395925539';
const YOUR_PHONE = '79992556031';
const YOUR_NAME = 'Елисеенко Илья Сергеевич';

async function testPersonalMessage() {
    console.log('🧪 Тестирование персонального сообщения...');
    
    try {
        const response = await axios.post(`${API_BASE}/messages/personal`, {
            agent_id: YOUR_AGENT_ID,
            message: `🧪 Тестовое персональное сообщение для ${YOUR_NAME}!\n\nВремя: ${new Date().toLocaleString('ru-RU')}\n\n✅ Если вы получили это сообщение, система работает!`,
            channel: 'telegram'
        });
        
        console.log('✅ Персональное сообщение отправлено:', response.data);
    } catch (error) {
        console.error('❌ Ошибка отправки персонального сообщения:', error.response?.data || error.message);
    }
}

async function testBulkMessage() {
    console.log('🧪 Тестирование массового сообщения...');
    
    // Сначала добавим вас в очередь для теста
    try {
        const response = await axios.post(`${API_BASE}/messages/bulk`, {
            queue_type: 'VIP-Frequent', // Попробуем эту очередь
            message: `📢 Тестовое массовое сообщение!\n\nВремя: ${new Date().toLocaleString('ru-RU')}\n\n✅ Если вы получили это сообщение, массовая рассылка работает!`,
            channel: 'telegram'
        });
        
        console.log('✅ Массовое сообщение отправлено:', response.data);
    } catch (error) {
        console.error('❌ Ошибка отправки массового сообщения:', error.response?.data || error.message);
    }
}

async function checkYourData() {
    console.log('📋 Ваши данные в системе:');
    console.log(`- Agent ID: ${YOUR_AGENT_ID}`);
    console.log(`- Telegram ID: ${YOUR_TG_ID}`);
    console.log(`- Телефон: ${YOUR_PHONE}`);
    console.log(`- Имя: ${YOUR_NAME}`);
    console.log('');
}

async function runTests() {
    console.log('🚀 Запуск тестов отправки сообщений...\n');
    
    await checkYourData();
    
    // Тестируем персональное сообщение
    await testPersonalMessage();
    console.log('');
    
    // Ждем 2 секунды между тестами
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Тестируем массовое сообщение
    await testBulkMessage();
    
    console.log('\n✅ Тесты завершены!');
    console.log('📱 Проверьте ваш Telegram на наличие тестовых сообщений.');
}

// Запускаем тесты
runTests().catch(console.error);
