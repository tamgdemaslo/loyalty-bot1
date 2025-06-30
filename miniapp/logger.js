/**
 * Простой модуль логирования для Mini App
 */

// Уровни логирования
const LOG_LEVELS = {
  ERROR: 0,
  WARN: 1,
  INFO: 2,
  DEBUG: 3
};

// Текущий уровень логирования (можно менять в зависимости от окружения)
const currentLevel = process.env.NODE_ENV === 'production' ? LOG_LEVELS.WARN : LOG_LEVELS.DEBUG;

/**
 * Форматирует дату для лога
 * @returns {string} Отформатированная дата
 */
function getFormattedDate() {
  const now = new Date();
  return `${now.toISOString().replace('T', ' ').substr(0, 19)}`;
}

/**
 * Логирование ошибок
 * @param {string} message - Сообщение для логирования
 */
function error(message) {
  if (currentLevel >= LOG_LEVELS.ERROR) {
    console.error(`[${getFormattedDate()}] ERROR: ${message}`);
  }
}

/**
 * Логирование предупреждений
 * @param {string} message - Сообщение для логирования
 */
function warn(message) {
  if (currentLevel >= LOG_LEVELS.WARN) {
    console.warn(`[${getFormattedDate()}] WARN: ${message}`);
  }
}

/**
 * Логирование информационных сообщений
 * @param {string} message - Сообщение для логирования
 */
function info(message) {
  if (currentLevel >= LOG_LEVELS.INFO) {
    console.info(`[${getFormattedDate()}] INFO: ${message}`);
  }
}

/**
 * Логирование отладочных сообщений
 * @param {string} message - Сообщение для логирования
 */
function debug(message) {
  if (currentLevel >= LOG_LEVELS.DEBUG) {
    console.debug(`[${getFormattedDate()}] DEBUG: ${message}`);
  }
}

module.exports = {
  error,
  warn,
  info,
  debug
};
