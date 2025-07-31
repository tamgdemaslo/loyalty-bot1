# loyalty-bot/bot/analytics.py
"""
Модуль аналитики и отчетов для системы лояльности
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .db import conn, get_agent_id, get_bonus_transactions
from .moysklad import fetch_shipments, fetch_demand_full
from .formatting import fmt_money, fmt_date_local
from .loyalty import get_level_info, LOYALTY_LEVELS


def get_client_statistics(agent_id: str) -> Dict:
    """
    Получает статистику клиента: траты, посещения, экономия
    """
    # Получаем все отгрузки клиента
    shipments = fetch_shipments(agent_id, limit=100)
    
    if not shipments:
        return {
            "total_spent": 0,
            "total_visits": 0,
            "total_saved": 0,
            "avg_check": 0,
            "first_visit": None,
            "last_visit": None,
            "visits_this_month": 0,
            "spent_this_month": 0,
            "period_days": 0
        }
    
    # Базовая статистика
    total_spent = sum(s["sum"] for s in shipments)
    total_visits = len(shipments)
    
    # Даты первого и последнего визита
    dates = [datetime.fromisoformat(s["moment"].replace("Z", "+00:00")) for s in shipments]
    first_visit = min(dates)
    last_visit = max(dates)
    period_days = (last_visit - first_visit).days + 1
    
    # Статистика за текущий месяц
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    visits_this_month = sum(1 for d in dates if d >= current_month)
    spent_this_month = sum(
        s["sum"] for s in shipments 
        if datetime.fromisoformat(s["moment"].replace("Z", "+00:00")) >= current_month
    )
    
    # Средний чек
    avg_check = total_spent // total_visits if total_visits > 0 else 0
    
    # Подсчитываем экономию (сколько бонусов было потрачено)
    # Используем новую таблицу транзакций для точного подсчета
    saved_transactions = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_saved
        FROM bonus_transactions
        WHERE agent_id = ? AND transaction_type = 'redemption'
    """, (agent_id,)).fetchone()
    
    total_saved = saved_transactions[0] if saved_transactions else 0
    
    return {
        "total_spent": total_spent,
        "total_visits": total_visits,
        "total_saved": total_saved,
        "avg_check": avg_check,
        "first_visit": first_visit,
        "last_visit": last_visit,
        "visits_this_month": visits_this_month,
        "spent_this_month": spent_this_month,
        "period_days": period_days
    }


def get_client_ranking(agent_id: str) -> Dict:
    """
    Получает рейтинг клиента среди всех клиентов
    """
    # Получаем общую сумму трат клиента
    client_spent = conn.execute(
        "SELECT total_spent FROM loyalty_levels WHERE agent_id = ?",
        (agent_id,)
    ).fetchone()
    
    if not client_spent:
        return {
            "rank": 0,
            "total_clients": 0,
            "percentile": 0,
            "spent_rank": 0
        }
    
    client_spent = client_spent[0]
    
    # Общее количество клиентов
    total_clients = conn.execute(
        "SELECT COUNT(*) FROM loyalty_levels"
    ).fetchone()[0]
    
    # Рейтинг по тратам (сколько клиентов потратили меньше)
    spent_rank = conn.execute(
        "SELECT COUNT(*) + 1 FROM loyalty_levels WHERE total_spent > ?",
        (client_spent,)
    ).fetchone()[0]
    
    # Процентиль
    percentile = ((total_clients - spent_rank + 1) / total_clients * 100) if total_clients > 0 else 0
    
    # Получаем топ-10 клиентов для сравнения
    top_clients = conn.execute("""
        SELECT 
            ll.agent_id,
            ll.total_spent,
            ll.level_id,
            um.fullname
        FROM loyalty_levels ll
        LEFT JOIN user_map um ON ll.agent_id = um.agent_id
        ORDER BY ll.total_spent DESC
        LIMIT 10
    """).fetchall()
    
    return {
        "rank": spent_rank,
        "total_clients": total_clients,
        "percentile": percentile,
        "spent_rank": spent_rank,
        "top_clients": [
            {
                "agent_id": row[0],
                "total_spent": row[1],
                "level_id": row[2],
                "fullname": row[3] or "Клиент"
            }
            for row in top_clients
        ]
    }


def get_bonus_history(agent_id: str, days: int = 30) -> List[Dict]:
    """
    Получает историю начислений и списаний бонусов
    """
    # Используем новую функцию из db.py для получения истории транзакций
    return get_bonus_transactions(agent_id, days)


def get_loyalty_distribution() -> Dict:
    """
    Получает распределение клиентов по уровням лояльности
    """
    distribution = conn.execute("""
        SELECT 
            level_id,
            COUNT(*) as count,
            AVG(total_spent) as avg_spent,
            MIN(total_spent) as min_spent,
            MAX(total_spent) as max_spent
        FROM loyalty_levels
        GROUP BY level_id
        ORDER BY level_id
    """).fetchall()
    
    result = {}
    total_clients = sum(row[1] for row in distribution)
    
    for row in distribution:
        level_id, count, avg_spent, min_spent, max_spent = row
        level_info = get_level_info(level_id)
        
        result[level_id] = {
            "name": level_info["name"],
            "emoji": level_info["emoji"],
            "count": count,
            "percentage": (count / total_clients * 100) if total_clients > 0 else 0,
            "avg_spent": int(avg_spent or 0),
            "min_spent": int(min_spent or 0),
            "max_spent": int(max_spent or 0)
        }
    
    return result


def format_client_statistics(stats: Dict) -> str:
    """
    Форматирует статистику клиента для отображения
    """
    if stats["total_visits"] == 0:
        return "📊 <b>Ваша статистика</b>\n\n📝 Пока нет данных о посещениях"
    
    # Частота посещений
    if stats["period_days"] > 0:
        visit_frequency = stats["total_visits"] / (stats["period_days"] / 30)  # посещений в месяц
        frequency_text = f"{visit_frequency:.1f} раз в месяц"
    else:
        frequency_text = "Недостаточно данных"
    
    text = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"💰 <b>Общие траты:</b> {fmt_money(stats['total_spent'])}\n"
        f"📈 <b>Количество посещений:</b> {stats['total_visits']}\n"
        f"💳 <b>Средний чек:</b> {fmt_money(stats['avg_check'])}\n"
        f"🎁 <b>Сэкономлено бонусами:</b> {fmt_money(stats['total_saved'])}\n\n"
        f"📅 <b>Первое посещение:</b> {fmt_date_local(stats['first_visit'].isoformat()) if stats['first_visit'] else 'Н/Д'}\n"
        f"📅 <b>Последнее посещение:</b> {fmt_date_local(stats['last_visit'].isoformat()) if stats['last_visit'] else 'Н/Д'}\n"
        f"🔄 <b>Частота посещений:</b> {frequency_text}\n\n"
        f"📊 <b>За текущий месяц:</b>\n"
        f"• Посещений: {stats['visits_this_month']}\n"
        f"• Потрачено: {fmt_money(stats['spent_this_month'])}"
    )
    
    return text


def format_client_ranking(ranking: Dict, agent_id: str) -> str:
    """
    Форматирует рейтинг клиента для отображения
    """
    if ranking["total_clients"] == 0:
        return "🏆 <b>Ваш рейтинг</b>\n\nНедостаточно данных для формирования рейтинга"
    
    # Определяем медаль
    if ranking["percentile"] >= 90:
        medal = "🥇"
        rank_desc = "Топ 10%"
    elif ranking["percentile"] >= 75:
        medal = "🥈"
        rank_desc = "Топ 25%"
    elif ranking["percentile"] >= 50:
        medal = "🥉"
        rank_desc = "Выше среднего"
    else:
        medal = "📊"
        rank_desc = "Растущий клиент"
    
    text = (
        f"🏆 <b>Ваш рейтинг среди клиентов</b>\n\n"
        f"{medal} <b>Позиция:</b> {ranking['rank']} из {ranking['total_clients']}\n"
        f"📊 <b>Процентиль:</b> {ranking['percentile']:.1f}% ({rank_desc})\n\n"
        f"<b>🔥 Топ-5 клиентов:</b>\n"
    )
    
    # Добавляем топ-5 клиентов
    for i, client in enumerate(ranking["top_clients"][:5], 1):
        level_info = get_level_info(client["level_id"])
        is_current = client["agent_id"] == agent_id
        marker = "👑" if is_current else f"{i}."
        
        text += (
            f"{marker} {level_info['emoji']} "
            f"{'<b>' if is_current else ''}"
            f"{client['fullname'][:15]}{'...' if len(client['fullname']) > 15 else ''} - "
            f"{fmt_money(client['total_spent'])}"
            f"{'</b>' if is_current else ''}\n"
        )
    
    return text


def format_bonus_history(history: List[Dict]) -> str:
    """
    Форматирует историю бонусов для отображения
    """
    if not history:
        return "📝 <b>История начислений и списаний</b>\n\nИстория пока пуста"
    
    text = "📝 <b>История бонусов (последние 30 дней)</b>\n\n"
    
    total_accrued = sum(h["amount"] for h in history if h["type"] == "accrual")
    total_redeemed = sum(h["amount"] for h in history if h["type"] == "redemption")
    
    text += (
        f"📊 <b>Итого за период:</b>\n"
        f"• Начислено: +{fmt_money(total_accrued)}\n"
        f"• Потрачено: -{fmt_money(total_redeemed)}\n\n"
        f"<b>Последние операции:</b>\n"
    )
    
    for transaction in history[:10]:  # Показываем последние 10 операций
        date_str = transaction["date"].strftime("%d.%m.%Y")
        
        if transaction["type"] == "accrual":
            emoji = "📈"
            sign = "+"
        else:
            emoji = "📉"
            sign = "-"
        
        text += (
            f"{emoji} {date_str} {sign}{fmt_money(transaction['amount'])}\n"
            f"   <i>{transaction['description']}</i>\n\n"
        )
    
    return text


def get_monthly_analytics() -> Dict:
    """
    Получает месячную аналитику по всем клиентам
    """
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Статистика по уровням
    level_stats = conn.execute("""
        SELECT 
            level_id,
            COUNT(*) as clients,
            SUM(total_spent) as total_revenue,
            AVG(total_spent) as avg_spent
        FROM loyalty_levels
        GROUP BY level_id
        ORDER BY level_id
    """).fetchall()
    
    # Общая статистика
    total_stats = conn.execute("""
        SELECT 
            COUNT(*) as total_clients,
            SUM(balance) as total_bonuses,
            AVG(balance) as avg_balance
        FROM bonuses
    """).fetchone()
    
    return {
        "level_distribution": {
            row[0]: {
                "clients": row[1],
                "revenue": row[2] or 0,
                "avg_spent": row[3] or 0
            }
            for row in level_stats
        },
        "total_clients": total_stats[0] if total_stats else 0,
        "total_bonuses": total_stats[1] if total_stats else 0,
        "avg_balance": total_stats[2] if total_stats else 0
    }
