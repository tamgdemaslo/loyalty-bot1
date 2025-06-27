import axios from 'axios';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Аутентификация
export const authService = {
  // Авторизация по номеру телефона
  async loginWithPhone(phone) {
    try {
      const response = await api.post('/auth/login', { phone });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Ошибка авторизации');
    }
  },

  // Регистрация нового пользователя
  async register(userData) {
    try {
      const response = await api.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Ошибка регистрации');
    }
  },

  // Проверка статуса авторизации
  async checkAuth(agentId) {
    try {
      const response = await api.get(`/auth/check/${agentId}`);
      return response.data;
    } catch (error) {
      throw new Error('Ошибка проверки авторизации');
    }
  }
};

// Пользователи
export const userService = {
  // Получение информации о пользователе
  async getUserInfo(agentId) {
    try {
      const response = await api.get(`/users/${agentId}`);
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения данных пользователя');
    }
  },

  // Получение баланса
  async getBalance(agentId) {
    try {
      const response = await api.get(`/users/${agentId}/balance`);
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения баланса');
    }
  },

  // Получение уровня лояльности
  async getLoyaltyLevel(agentId) {
    try {
      const response = await api.get(`/users/${agentId}/loyalty`);
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения уровня лояльности');
    }
  }
};

// Транзакции
export const transactionService = {
  // Получение истории транзакций
  async getTransactions(agentId, params = {}) {
    try {
      const response = await api.get(`/transactions`, {
        params: { agent_id: agentId, ...params }
      });
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения истории транзакций');
    }
  },

  // Списание бонусов
  async redeemBonuses(agentId, amount, description) {
    try {
      const response = await api.post(`/users/${agentId}/balance`, {
        amount: -Math.abs(amount),
        description
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Ошибка списания бонусов');
    }
  }
};

// Отгрузки/покупки
export const shipmentService = {
  // Получение истории покупок
  async getShipments(agentId, params = {}) {
    try {
      const response = await api.get(`/shipments/${agentId}`, { params });
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения истории покупок');
    }
  },

  // Получение детальной информации о покупке
  async getShipmentDetail(shipmentId) {
    try {
      const response = await api.get(`/shipments/detail/${shipmentId}`);
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения детальной информации');
    }
  }
};

// Запись на услуги
export const bookingService = {
  // Получение списка услуг
  async getServices() {
    try {
      const response = await api.get('/booking/services');
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения списка услуг');
    }
  },

  // Получение списка мастеров
  async getStaff() {
    try {
      const response = await api.get('/booking/staff');
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения списка мастеров');
    }
  },

  // Получение свободных слотов
  async getFreeSlots(serviceId, staffId, date) {
    try {
      const response = await api.get('/booking/slots', {
        params: { service_id: serviceId, staff_id: staffId, date }
      });
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения свободных слотов');
    }
  },

  // Создание записи
  async createBooking(bookingData) {
    try {
      const response = await api.post('/booking/create', bookingData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Ошибка создания записи');
    }
  },

  // Получение записей пользователя
  async getUserBookings(agentId) {
    try {
      const response = await api.get(`/booking/user/${agentId}`);
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения записей');
    }
  }
};

// Аналитика
export const analyticsService = {
  // Получение статистики пользователя
  async getUserStats(agentId) {
    try {
      const response = await api.get(`/analytics/user/${agentId}`);
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения статистики');
    }
  },

  // Получение рейтинга пользователя
  async getUserRanking(agentId) {
    try {
      const response = await api.get(`/analytics/ranking/${agentId}`);
      return response.data;
    } catch (error) {
      throw new Error('Ошибка получения рейтинга');
    }
  }
};

export default api;
