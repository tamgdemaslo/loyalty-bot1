/**
 * Скрипт для модификации server.js для использования PostgreSQL вместо SQLite
 * 
 * Этот скрипт заменяет импорт api_integration.js на api_postgres.js
 * в файле server.js, чтобы использовать новую реализацию для PostgreSQL.
 */

const fs = require('fs');
const path = require('path');

// Путь к файлу server.js
const serverFilePath = path.join(__dirname, 'server.js');

// Проверка существования файла
if (!fs.existsSync(serverFilePath)) {
  console.error('Ошибка: Файл server.js не найден');
  process.exit(1);
}

// Чтение содержимого файла
let serverContent = fs.readFileSync(serverFilePath, 'utf8');

// Замена импорта модуля
if (serverContent.includes("const db = require('./api_integration')")) {
  serverContent = serverContent.replace(
    "const db = require('./api_integration')",
    "const db = require('./api_postgres')"
  );
  
  console.log('Импорт модуля успешно заменен');
} else if (serverContent.includes("const db = require('./api_integration_simple')")) {
  serverContent = serverContent.replace(
    "const db = require('./api_integration_simple')",
    "const db = require('./api_postgres')"
  );
  
  console.log('Импорт модуля успешно заменен');
} else {
  console.error('Ошибка: Не найден импорт модуля api_integration в файле server.js');
  process.exit(1);
}

// Запись обновленного содержимого обратно в файл
try {
  fs.writeFileSync(serverFilePath, serverContent, 'utf8');
  console.log('Файл server.js успешно обновлен для использования PostgreSQL');
} catch (error) {
  console.error(`Ошибка при записи файла: ${error.message}`);
  process.exit(1);
}

// Проверка наличия .env.postgres файла
const envFilePath = path.join(__dirname, '.env.postgres');
if (!fs.existsSync(envFilePath)) {
  console.warn('Предупреждение: Файл .env.postgres не найден. Убедитесь, что он создан и содержит настройки подключения к PostgreSQL');
}

console.log('\nВсе изменения выполнены. Необходимо выполнить следующие шаги:');
console.log('1. Убедитесь, что файл .env.postgres содержит корректные данные для подключения к PostgreSQL');
console.log('2. Установите необходимые зависимости: npm install pg');
console.log('3. Перезапустите сервер: node server.js');
