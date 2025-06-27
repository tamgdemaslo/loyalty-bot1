import logging
import asyncio
from datetime import datetime, timezone
from aiogram import Bot
from .config import BOT_TOKEN, BONUS_RATE, MS_BASE, MSK
from .db import change_balance, conn, get_tg_id_by_agent, get_loyalty_level, update_total_spent, add_bonus_transaction
from .formatting import fmt_money
from .moysklad import fetch_demands, fetch_demand_full
from .loyalty import get_bonus_rate, get_level_up_message
from dateutil import parser as dateparser, relativedelta

log = logging.getLogger(__name__)

def doc_age_seconds(iso: str) -> float:
    ts = dateparser.isoparse(iso).replace(tzinfo=MSK)
    return (datetime.now(MSK) - ts).total_seconds()

async def notify_user_about_demand(demand: dict, bonus_amount: int):
    """Отправляет уведомление пользователю о готовой машине и бонусах"""
    try:
        # Получаем agent_id из demand
        agent_id = demand["agent"]["meta"]["href"].split("/")[-1]
        # Получаем tg_id пользователя
        tg_id = get_tg_id_by_agent(agent_id)
        
        if tg_id:
            bot = Bot(token=BOT_TOKEN)
            try:
                message = (
                    "🚗 <b>Ваша машина готова!</b>\n\n"
                    f"💰 Сумма к оплате: <b>{fmt_money(demand['sum'])}</b>\n"
                    f"✨ Будет начислено бонусов: <b>{fmt_money(bonus_amount)}</b>"
                )
                await bot.send_message(
                    chat_id=tg_id,
                    text=message,
                    parse_mode="HTML"
                )
                log.info(f"Notification sent to user {tg_id}")
            except Exception as e:
                log.error(f"Failed to send notification: {e}")
            finally:
                await bot.session.close()
    except Exception as e:
        log.error(f"Error in notify_user_about_demand: {e}")


async def notify_user_about_purchase(demand: dict, bonus_amount: int, level_id: int):
    """Отправляет уведомление о начислении бонусов с учетом уровня"""
    from .loyalty import get_level_info
    
    try:
        agent_id = demand["agent"]["meta"]["href"].split("/")[-1]
        tg_id = get_tg_id_by_agent(agent_id)
        
        if tg_id:
            bot = Bot(token=BOT_TOKEN)
            try:
                level_info = get_level_info(level_id)
                message = (
                    f"🚗 <b>Ваша машина готова!</b>\n\n"
                    f"💰 Сумма к оплате: <b>{fmt_money(demand['sum'])}</b>\n"
                    f"✨ Начислено бонусов: <b>{fmt_money(bonus_amount)}</b>\n"
                    f"🏆 Ваш статус: {level_info['emoji']} <b>{level_info['name']}</b> ({level_info['bonus_rate']*100:.0f}% бонусов)"
                )
                await bot.send_message(
                    chat_id=tg_id,
                    text=message,
                    parse_mode="HTML"
                )
                log.info(f"Purchase notification sent to user {tg_id}")
            except Exception as e:
                log.error(f"Failed to send purchase notification: {e}")
            finally:
                await bot.session.close()
    except Exception as e:
        log.error(f"Error in notify_user_about_purchase: {e}")


async def notify_level_up(agent_id: str, old_level: int, new_level: int):
    """Отправляет уведомление о повышении уровня лояльности"""
    try:
        tg_id = get_tg_id_by_agent(agent_id)
        
        if tg_id:
            bot = Bot(token=BOT_TOKEN)
            try:
                message = get_level_up_message(old_level, new_level)
                await bot.send_message(
                    chat_id=tg_id,
                    text=message,
                    parse_mode="HTML"
                )
                log.info(f"Level up notification sent to user {tg_id} (level {old_level} -> {new_level})")
            except Exception as e:
                log.error(f"Failed to send level up notification: {e}")
            finally:
                await bot.session.close()
    except Exception as e:
        log.error(f"Error in notify_level_up: {e}")

async def accrue_for_demand(demand: dict) -> int:
    aid = demand["agent"]["meta"]["href"].split("/")[-1]
    
    # Получаем текущий уровень клиента
    loyalty_data = get_loyalty_level(aid)
    current_level = loyalty_data["level_id"]
    bonus_rate = get_bonus_rate(current_level)
    
    # Получаем пробег из атрибутов отгрузки
    mileage = 0
    attributes = demand.get('attributes', [])
    for attr in attributes:
        if attr.get('name') == 'Пробег':
            mileage_str = str(attr.get('value', '0'))
            mileage_clean = ''.join(filter(str.isdigit, mileage_str))
            mileage = int(mileage_clean) if mileage_clean else 0
            break
    
    # Рассчитываем сумму покупки (только товары, не услуги)
    purchase_amount = 0
    bonus_amount = 0
    services = []  # Собираем услуги для анализа ТО
    
    for p in demand["positions"]["rows"]:
        item_total = int(p["price"] * p["quantity"])
        purchase_amount += item_total
        
        # Начисляем бонусы только с товаров
        if p["assortment"]["meta"]["type"] != "service":
            bonus_amount += int(item_total * bonus_rate)
        else:
            # Собираем услуги для анализа ТО
            services.append(p)
    
    if bonus_amount > 0:
        # Начисляем бонусы
        change_balance(aid, bonus_amount)
        
        # Записываем транзакцию
        description = f"Начисление за чек №{demand.get('name', demand['id'][:8])}"
        add_bonus_transaction(aid, "accrual", bonus_amount, description, demand['id'])
        
        # Обновляем общую сумму трат и проверяем повышение уровня
        level_update = update_total_spent(aid, purchase_amount)
        
        log.info("Accrued %s (rate: %.1f%%) → %s", fmt_money(bonus_amount), bonus_rate*100, aid)
        
        # Отправляем уведомление о начислении
        await notify_user_about_purchase(demand, bonus_amount, current_level)
        
        # Если уровень повысился, отправляем отдельное уведомление
        if level_update["level_changed"]:
            await notify_level_up(aid, level_update["old_level"], level_update["new_level"])
    
    # Анализируем услуги для автоматической записи в журнал ТО
    if services and mileage > 0:
        try:
            from .maintenance import process_moysklad_services
            # Получаем дату отгрузки в формате YYYY-MM-DD
            demand_date = datetime.fromisoformat(demand["moment"].replace("Z", "+00:00")).strftime("%Y-%m-%d")
            process_moysklad_services(aid, demand["id"], services, mileage, demand_date)
            log.info(f"Processed {len(services)} services for maintenance tracking")
        except Exception as e:
            log.error(f"Error processing maintenance services: {e}")
    
    return bonus_amount

async def accrual_loop():
    """Основной цикл начисления бонусов"""
    log.info("Accrual loop started...")
    while True:
        try:
            # Получаем последние отгрузки
            demands = fetch_demands(limit=10)
            for demand in demands:
                # Проверяем, обработана ли уже эта отгрузка
                already = conn.execute(
                    "SELECT 1 FROM accrual_log WHERE demand_id=?",
                    (demand["id"],)
                ).fetchone()
                
                if not already:
                    # Если отгрузка новая - начисляем бонусы и отправляем уведомление
                    bonus_amount = await accrue_for_demand(demand)
                    if bonus_amount > 0:
                        await notify_user_about_demand(demand, bonus_amount)
                        conn.execute(
                            "INSERT INTO accrual_log(demand_id) VALUES(?)",
                            (demand["id"],)
                        )
                        conn.commit()
        
        except Exception as e:
            log.error(f"Error in accrual loop: {e}")
        
        # Ждем 5 минут перед следующей проверкой
        await asyncio.sleep(30)
