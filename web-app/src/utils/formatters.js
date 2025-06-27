import { format, parseISO, isValid } from 'date-fns';
import { ru } from 'date-fns/locale';

// Форматирование денежных сумм
export const formatMoney = (amount) => {
  if (!amount && amount !== 0) return '0 ₽';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

// Форматирование бонусов
export const formatBonuses = (amount) => {
  if (!amount && amount !== 0) return '0';
  return new Intl.NumberFormat('ru-RU').format(amount);
};

// Форматирование даты
export const formatDate = (date, formatString = 'dd.MM.yyyy') => {
  if (!date) return '';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) return '';
    
    return format(dateObj, formatString, { locale: ru });
  } catch (error) {
    console.error('Error formatting date:', error);
    return '';
  }
};

// Форматирование даты и времени
export const formatDateTime = (date) => {
  return formatDate(date, 'dd.MM.yyyy HH:mm');
};

// Форматирование относительной даты
export const formatRelativeDate = (date) => {
  if (!date) return '';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    const now = new Date();
    const diffMs = now - dateObj;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Сегодня';
    if (diffDays === 1) return 'Вчера';
    if (diffDays < 7) return `${diffDays} дн. назад`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} нед. назад`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} мес. назад`;
    
    return `${Math.floor(diffDays / 365)} г. назад`;
  } catch (error) {
    return formatDate(date);
  }
};

// Форматирование номера телефона
export const formatPhone = (phone) => {
  if (!phone) return '';
  
  // Убираем все символы кроме цифр
  const digits = phone.replace(/\D/g, '');
  
  // Если номер начинается с 8, заменяем на +7
  const normalizedDigits = digits.startsWith('8') ? '7' + digits.slice(1) : digits;
  
  // Форматируем как +7 (XXX) XXX-XX-XX
  if (normalizedDigits.length === 11 && normalizedDigits.startsWith('7')) {
    return `+7 (${normalizedDigits.slice(1, 4)}) ${normalizedDigits.slice(4, 7)}-${normalizedDigits.slice(7, 9)}-${normalizedDigits.slice(9, 11)}`;
  }
  
  return phone;
};

// Получение названия уровня лояльности
export const getLevelName = (level) => {
  const levels = {
    1: 'Новичок',
    2: 'Постоянный',
    3: 'Бронзовый',
    4: 'Серебряный',
    5: 'Золотой'
  };
  
  return levels[level] || 'Неизвестный';
};

// Получение цвета уровня лояльности
export const getLevelColor = (level) => {
  const colors = {
    1: 'gray',
    2: 'blue',
    3: 'green',
    4: 'yellow',
    5: 'purple'
  };
  
  return colors[level] || 'gray';
};

// Форматирование процентов
export const formatPercent = (value, decimals = 1) => {
  if (!value && value !== 0) return '0%';
  return `${value.toFixed(decimals)}%`;
};

// Сокращение длинного текста
export const truncateText = (text, maxLength = 50) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

// Форматирование типа транзакции
export const formatTransactionType = (type) => {
  const types = {
    'accrual': 'Начисление',
    'redemption': 'Списание',
    'bonus': 'Бонус',
    'purchase': 'Покупка',
    'refund': 'Возврат'
  };
  
  return types[type] || type;
};

// Получение иконки для типа транзакции
export const getTransactionIcon = (type) => {
  const icons = {
    'accrual': '➕',
    'redemption': '➖',
    'bonus': '🎁',
    'purchase': '🛒',
    'refund': '↩️'
  };
  
  return icons[type] || '💰';
};

// Форматирование статуса записи
export const formatBookingStatus = (status) => {
  const statuses = {
    'confirmed': 'Подтверждена',
    'pending': 'Ожидает подтверждения',
    'cancelled': 'Отменена',
    'completed': 'Завершена',
    'no_show': 'Не явился'
  };
  
  return statuses[status] || status;
};

// Получение цвета статуса записи
export const getBookingStatusColor = (status) => {
  const colors = {
    'confirmed': 'green',
    'pending': 'yellow',
    'cancelled': 'red',
    'completed': 'blue',
    'no_show': 'gray'
  };
  
  return colors[status] || 'gray';
};
