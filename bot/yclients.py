# loyalty-bot/bot/yclients.py
import requests
import locale
import logging
from datetime import date
from typing import Dict, List, Optional
from requests.exceptions import ConnectionError, Timeout, HTTPError

from .config import YCLIENTS_PARTNER_TOKEN
from .exceptions import YClientsError, RetryableError, ValidationError
from .utils import retry_on_failure, handle_api_response, safe_get_nested

API = "https://api.yclients.com/api/v1"
HEADERS = {
    "Authorization": f"Bearer {YCLIENTS_PARTNER_TOKEN}",
    "Accept":        "application/vnd.yclients.v2+json",
    "Content-Type":  "application/json",
}


# Настройка логирования
log = logging.getLogger(__name__)

# ─────────────────────────── helpers ────────────────────────────
@retry_on_failure(retries=3, wait_time=1.0, exceptions=(ConnectionError, Timeout, RetryableError))
def _get(path: str, params: dict | None = None) -> dict:
    """
    Внутренний GET с улучшенной обработкой ошибок: всегда возвращаем только data из ответа
    
    Args:
        path: путь к API endpoint
        params: параметры запроса
    
    Returns:
        dict: данные из поля 'data' ответа API
    
    Raises:
        YClientsError: при ошибках API YCLIENTS
        RetryableError: при временных ошибках, которые можно повторить
    """
    url = API + path
    
    try:
        log.debug(f"Making request to YCLIENTS: {url}")
        response = requests.get(
            url, 
            headers=HEADERS, 
            params=params or {}, 
            timeout=10
        )
        
        result = handle_api_response(response, "YCLIENTS")
        return safe_get_nested(result, "data", default={})
        
    except (ConnectionError, Timeout) as e:
        error_msg = f"Network error for YCLIENTS API ({url}): {e}"
        log.warning(error_msg)
        raise RetryableError(error_msg)
    except HTTPError as e:
        if e.response.status_code >= 500:
            error_msg = f"YCLIENTS server error ({url}): {e}"
            log.warning(error_msg)
            raise RetryableError(error_msg)
        else:
            error_msg = f"YCLIENTS client error ({url}): {e}"
            log.error(error_msg)
            raise YClientsError(error_msg, status_code=e.response.status_code)
    except Exception as e:
        error_msg = f"Unexpected error for YCLIENTS API ({url}): {e}"
        log.error(error_msg)
        raise YClientsError(error_msg)

def book_dates(company_id: int, **params) -> dict:
    """
    GET /book_dates/{company_id}
    Возвращает словарь с ключами booking_dates, booking_days, …
    """
    return _get(f"/book_dates/{company_id}", params)


def _post(path: str, json: dict):
    """Внутренний POST: всегда возвращаем только data из ответа."""
    r = requests.post(API + path, headers=HEADERS, json=json, timeout=10)
    r.raise_for_status()
    return r.json()["data"]          # <-- берём ровно data


def format_date_russian(date_iso: str) -> str:
    """Форматирует дату с русскими месяцами."""
    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
    return date.fromisoformat(date_iso).strftime("%d %b (%a)")


# ───────────────────── публичные обёртки API ────────────────────
def services(company_id: int):
    """GET /book_services/{company_id}"""
    return _get(f"/book_services/{company_id}")


def staff(company_id: int, service_ids: list[int] | None = None):
    """GET /book_staff/{company_id}"""
    params = {}
    if service_ids:
        params["service_ids[]"] = service_ids
    return _get(f"/book_staff/{company_id}", params)


def free_slots(
    company_id: int,
    staff_id:   int,
    service_id: int,
    date_iso:   str,
) -> list[dict]:
    """
    GET /book_times/{company_id}/{staff_id}/{date}
    Возвращает список словарей вида:
        {"time": "17:30", "datetime": "2025-06-17T14:30:00+03:00"}
    """
    return _get(
        f"/book_times/{company_id}/{staff_id}/{date_iso}",
        params={"service_ids[]": service_id},
    )


def create_record(
    company_id:      int,
    phone:           str,
    fullname:        str,
    email:           str,
    appointments:    list[dict],
    comment:         str | None = None,
    code:            str | None = None,
    notify_by_sms:   int | None = None,
    notify_by_email: int | None = None,
):
    """POST /book_record/{company_id}"""
    payload = {
        "phone":        phone,
        "fullname":     fullname,
        "email":        email,
        "appointments": appointments,
    }
    if comment:             payload["comment"]          = comment
    if code:                payload["code"]             = code
    if notify_by_sms is not None:
        payload["notify_by_sms"] = notify_by_sms
    if notify_by_email is not None:
        payload["notify_by_email"] = notify_by_email

    return _post(f"/book_record/{company_id}", payload)


# ───── совместимость со старым кодом ─────
def book_services(company_id: int, **params):
    """Старое имя функции — оставляем алиас для совместимости."""

    return services(company_id, **params)
