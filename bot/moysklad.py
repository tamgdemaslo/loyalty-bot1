import requests
import logging
from typing import Optional
from datetime import datetime, timedelta
from requests.exceptions import ConnectionError, Timeout, HTTPError

from .config import MS_BASE, HEADERS
from .exceptions import MoySkladError, RetryableError, ValidationError
from .utils import retry_on_failure, handle_api_response, safe_get_nested, validate_phone

MS_BASE = "https://api.moysklad.ru/api/remap/1.2"

# Настройка логирования
log = logging.getLogger(__name__)

@retry_on_failure(retries=3, wait_time=1.0, exceptions=(ConnectionError, Timeout, RetryableError))
def _get(path: str, params: dict | None = None) -> dict:
    """
    Выполняет GET-запрос к API МойСклад с retry-механизмом
    
    Args:
        path: путь к API endpoint
        params: параметры запроса
    
    Returns:
        dict: ответ API в формате JSON
    
    Raises:
        MoySkladError: при ошибках API МойСклад
        RetryableError: при временных ошибках, которые можно повторить
    """
    url = f"{MS_BASE}/{path.lstrip('/')}"
    
    try:
        log.debug(f"Making request to MoySklad: {url}")
        response = requests.get(
            url,
            headers=HEADERS,
            params=params or {},
            timeout=10
        )
        
        return handle_api_response(response, "MoySklad")
        
    except (ConnectionError, Timeout) as e:
        error_msg = f"Network error for MoySklad API ({url}): {e}"
        log.warning(error_msg)
        raise RetryableError(error_msg)
    except HTTPError as e:
        if e.response.status_code >= 500:
            error_msg = f"MoySklad server error ({url}): {e}"
            log.warning(error_msg)
            raise RetryableError(error_msg)
        else:
            error_msg = f"MoySklad client error ({url}): {e}"
            log.error(error_msg)
            raise MoySkladError(error_msg, status_code=e.response.status_code)
    except Exception as e:
        error_msg = f"Unexpected error for MoySklad API ({url}): {e}"
        log.error(error_msg)
        raise MoySkladError(error_msg)

def find_agent_by_phone(phone: str) -> Optional[str]:
    """
    Ищет контрагента по номеру телефона
    
    Args:
        phone: номер телефона
    
    Returns:
        str или None: ID контрагента или None если не найден
    
    Raises:
        ValidationError: если номер телефона некорректный
        MoySkladError: при ошибках API
    """
    try:
        digits = validate_phone(phone)
        log.debug(f"Searching agent by phone: {digits}")
        
        result = _get("entity/counterparty", {"search": digits, "limit": 1})
        rows = safe_get_nested(result, "rows", default=[])
        
        if rows:
            agent_id = rows[0].get("id")
            log.info(f"Found agent {agent_id} for phone {digits}")
            return agent_id
        else:
            log.info(f"No agent found for phone {digits}")
            return None
            
    except ValidationError:
        raise
    except Exception as e:
        log.error(f"Error finding agent by phone {phone}: {e}")
        raise MoySkladError(f"Failed to find agent by phone: {e}")

def fetch_shipments(agent_id: str, limit: int = 20, order: str = "desc") -> list[dict]:
    """
    Получает список отгрузок для контрагента
    
    Args:
        agent_id: ID контрагента
        limit: максимальное количество отгрузок
        order: порядок сортировки (asc/desc)
    
    Returns:
        list[dict]: список отгрузок
    
    Raises:
        MoySkladError: при ошибках API
    """
    if not agent_id:
        raise ValidationError("Agent ID не может быть пустым")
    
    try:
        log.debug(f"Fetching shipments for agent {agent_id}, limit={limit}")
        
        params = {
            "filter": f"agent={MS_BASE}/entity/counterparty/{agent_id}",
            "order": f"moment,{order}",
            "limit": limit,
            "expand": "state"
        }
        
        result = _get("entity/demand", params)
        shipments = safe_get_nested(result, "rows", default=[])
        
        # Фильтруем удаленные отгрузки с улучшенной обработкой ошибок
        valid_shipments = []
        for shipment in shipments:
            try:
                shipment_id = shipment.get("id")
                if not shipment_id:
                    log.warning("Shipment without ID found, skipping")
                    continue
                    
                # Проверяем, что отгрузка существует
                if fetch_demand_full(shipment_id):
                    valid_shipments.append(shipment)
                    
            except Exception as e:
                log.warning(f"Error checking shipment {shipment.get('id', 'unknown')}: {e}")
                continue
        
        log.info(f"Found {len(valid_shipments)} valid shipments for agent {agent_id}")
        return valid_shipments
        
    except Exception as e:
        log.error(f"Error fetching shipments for agent {agent_id}: {e}")
        raise MoySkladError(f"Failed to fetch shipments: {e}")

def fetch_demand_full(did: str) -> Optional[dict]:
    """
    Получает полную информацию об отгрузке с улучшенной обработкой ошибок
    
    Args:
        did: ID отгрузки
    
    Returns:
        dict или None: данные отгрузки или None если отгрузка не найдена
    
    Raises:
        ValidationError: если ID отгрузки пустой
        MoySkladError: при ошибках API (кроме 404)
    """
    if not did:
        raise ValidationError("Demand ID не может быть пустым")
    
    try:
        log.debug(f"Fetching demand details for {did}")
        result = _get(f"entity/demand/{did}", {
            "expand": "positions,positions.assortment,agent,state,attributes"
        })
        log.debug(f"Successfully fetched demand {did}")
        return result
        
    except MoySkladError as e:
        if hasattr(e, 'status_code') and e.status_code == 404:
            log.info(f"Demand not found: {did}")
            return None
        log.error(f"MoySklad error fetching demand {did}: {e}")
        raise
    except Exception as e:
        log.error(f"Unexpected error fetching demand {did}: {e}")
        raise MoySkladError(f"Failed to fetch demand details: {e}")

@retry_on_failure(retries=3, wait_time=1.0, exceptions=(ConnectionError, Timeout, RetryableError))
def apply_discount(did: str, percent: float, positions: list) -> dict:
    """
    Применяет скидку к отгрузке с улучшенной обработкой ошибок
    
    Args:
        did: ID отгрузки
        percent: процент скидки
        positions: список позиций для применения скидки
    
    Returns:
        dict: результат применения скидки
    
    Raises:
        ValidationError: при некорректных параметрах
        MoySkladError: при ошибках API
    """
    if not did:
        raise ValidationError("Demand ID не может быть пустым")
    
    if not isinstance(percent, (int, float)) or percent < 0 or percent > 100:
        raise ValidationError(f"Некорректный процент скидки: {percent}")
    
    if not positions:
        raise ValidationError("Список позиций не может быть пустым")
    
    try:
        log.debug(f"Applying {percent}% discount to demand {did}")
        
        # Валидируем позиции
        discount_positions = []
        for pos in positions:
            pos_id = pos.get("id")
            if not pos_id:
                log.warning(f"Position without ID found, skipping: {pos}")
                continue
            discount_positions.append({"id": pos_id, "discount": percent})
        
        if not discount_positions:
            raise ValidationError("Нет валидных позиций для применения скидки")
        
        body = {"positions": discount_positions}
        
        response = requests.put(
            f"{MS_BASE}/entity/demand/{did}",
            headers=HEADERS,
            json=body,
            timeout=10
        )
        
        result = handle_api_response(response, "MoySklad")
        log.info(f"Successfully applied {percent}% discount to demand {did}")
        return result
        
    except (ConnectionError, Timeout) as e:
        error_msg = f"Network error applying discount to {did}: {e}"
        log.warning(error_msg)
        raise RetryableError(error_msg)
    except HTTPError as e:
        if e.response.status_code >= 500:
            error_msg = f"Server error applying discount to {did}: {e}"
            log.warning(error_msg)
            raise RetryableError(error_msg)
        else:
            error_msg = f"Client error applying discount to {did}: {e}"
            log.error(error_msg)
            raise MoySkladError(error_msg, status_code=e.response.status_code)
    except Exception as e:
        log.error(f"Unexpected error applying discount to {did}: {e}")
        raise MoySkladError(f"Failed to apply discount: {e}")

def fetch_demands(limit: int = 10) -> list[dict]:
    """
    Получает список последних отгрузок с улучшенной обработкой ошибок
    
    Args:
        limit: максимальное количество отгрузок
    
    Returns:
        list[dict]: список отгрузок, отсортированный по дате по убыванию
    
    Raises:
        ValidationError: при некорректном лимите
        MoySkladError: при ошибках API
    """
    if not isinstance(limit, int) or limit <= 0:
        raise ValidationError(f"Некорректный лимит: {limit}")
    
    params = {
        "limit": min(limit, 1000),  # Ограничиваем максимальный лимит
        "order": "moment,desc",
        "filter": "state.name=Отгружен",
        "expand": "agent,positions,positions.assortment"
    }
    
    try:
        log.debug(f"Fetching {limit} demands from MoySklad")
        result = _get("entity/demand", params)
        demands = safe_get_nested(result, "rows", default=[])
        
        log.info(f"Successfully fetched {len(demands)} demands")
        return demands
        
    except Exception as e:
        log.error(f"Error fetching demands: {e}")
        raise MoySkladError(f"Failed to fetch demands: {e}")
