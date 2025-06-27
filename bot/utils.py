"""
Утилиты для retry-механизмов и обработки ошибок
"""
import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any, TypeVar, Union
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

from .exceptions import NetworkError, RetryableError, APIError

log = logging.getLogger(__name__)

T = TypeVar('T')


def retry_on_failure(
    retries: int = 3,
    wait_time: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (ConnectionError, Timeout, RetryableError)
):
    """
    Декоратор для повтора выполнения функции при ошибках
    
    Args:
        retries: количество попыток
        wait_time: начальное время ожидания между попытками
        backoff_factor: множитель увеличения времени ожидания
        exceptions: типы исключений, при которых нужно повторять
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_wait = wait_time
            
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        log.error(f"Function {func.__name__} failed after {retries} retries: {e}")
                        break
                    
                    log.warning(f"Attempt {attempt + 1}/{retries + 1} failed for {func.__name__}: {e}")
                    time.sleep(current_wait)
                    current_wait *= backoff_factor
                except Exception as e:
                    # Не повторяем для других типов ошибок
                    log.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            
            raise last_exception
        return wrapper
    return decorator


def async_retry_on_failure(
    retries: int = 3,
    wait_time: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (ConnectionError, Timeout, RetryableError)
):
    """
    Асинхронный декоратор для повтора выполнения функции при ошибках
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_wait = wait_time
            
            for attempt in range(retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        log.error(f"Async function {func.__name__} failed after {retries} retries: {e}")
                        break
                    
                    log.warning(f"Async attempt {attempt + 1}/{retries + 1} failed for {func.__name__}: {e}")
                    await asyncio.sleep(current_wait)
                    current_wait *= backoff_factor
                except Exception as e:
                    log.error(f"Non-retryable error in async {func.__name__}: {e}")
                    raise
            
            raise last_exception
        return wrapper
    return decorator


def handle_api_response(response: requests.Response, api_name: str = "API") -> dict:
    """
    Обрабатывает ответ API и возвращает JSON или выбрасывает соответствующее исключение
    
    Args:
        response: объект ответа requests
        api_name: название API для логирования
    
    Returns:
        dict: декодированный JSON ответ
    
    Raises:
        APIError: при ошибках API
    """
    try:
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        status_code = response.status_code
        try:
            error_data = response.json()
        except:
            error_data = {"error": response.text}
        
        error_msg = f"{api_name} HTTP {status_code}: {error_data}"
        log.error(error_msg)
        
        # Определяем, можно ли повторить запрос
        if status_code >= 500 or status_code == 429:  # Server errors or rate limit
            raise RetryableError(error_msg)
        else:
            raise APIError(error_msg, status_code=status_code, response_data=error_data)
    except requests.exceptions.JSONDecodeError as e:
        error_msg = f"{api_name} JSON decode error: {e}"
        log.error(error_msg)
        raise APIError(error_msg)


def safe_get_nested(data: dict, *keys, default=None) -> Any:
    """
    Безопасно получает вложенное значение из словаря
    
    Args:
        data: исходный словарь
        *keys: последовательность ключей для доступа к вложенному значению
        default: значение по умолчанию
    
    Returns:
        Значение или default если ключ не найден
    """
    try:
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError, IndexError):
        return default


def validate_phone(phone: str) -> str:
    """
    Валидирует и нормализует номер телефона
    
    Args:
        phone: номер телефона
    
    Returns:
        str: нормализованный номер телефона
    
    Raises:
        ValidationError: если номер некорректный
    """
    from .exceptions import ValidationError
    
    if not phone:
        raise ValidationError("Номер телефона не может быть пустым")
    
    # Удаляем все кроме цифр
    digits = "".join(filter(str.isdigit, phone))
    
    if len(digits) < 10:
        raise ValidationError(f"Номер телефона слишком короткий: {phone}")
    
    if len(digits) > 12:
        raise ValidationError(f"Номер телефона слишком длинный: {phone}")
    
    return digits


def log_function_call(func_name: str, args: tuple = None, kwargs: dict = None, result: Any = None, error: Exception = None):
    """
    Логирует вызов функции с параметрами и результатом
    """
    if error:
        log.error(f"Function {func_name} failed with error: {error}")
    else:
        log.debug(f"Function {func_name} completed successfully")
