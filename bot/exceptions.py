"""
Кастомные исключения для loyalty-bot
"""

class LoyaltyBotError(Exception):
    """Базовое исключение для всех ошибок бота"""
    pass


class APIError(LoyaltyBotError):
    """Базовое исключение для API-ошибок"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class MoySkladError(APIError):
    """Ошибки API МойСклад"""
    pass


class YClientsError(APIError):
    """Ошибки API YCLIENTS"""
    pass


class DatabaseError(LoyaltyBotError):
    """Ошибки базы данных"""
    pass


class UserNotFoundError(LoyaltyBotError):
    """Пользователь не найден"""
    pass


class InsufficientBalanceError(LoyaltyBotError):
    """Недостаточно бонусов на счету"""
    pass


class ValidationError(LoyaltyBotError):
    """Ошибки валидации данных"""
    pass


class NetworkError(LoyaltyBotError):
    """Сетевые ошибки"""
    pass


class RetryableError(LoyaltyBotError):
    """Ошибка, которую можно повторить"""
    pass
