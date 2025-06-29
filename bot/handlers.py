import logging
import requests
from datetime import datetime, timedelta, date
from aiogram import types, F
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardMarkup, InlineKeyboardBuilder
from bot.yclients import services, staff, free_slots, book_dates, create_record, format_date_russian
from bot.keyboards import shipments_kb, main_menu_premium, balance_detail_kb, profile_menu_kb, support_menu_kb, start_choice_kb, mini_app_menu_kb
from bot.db import register_mapping, user_contact
from bot.config import REDEEM_CAP, MINIAPP_URL
from bot.db import (get_agent_id, register_mapping, get_balance, change_balance, conn, get_loyalty_level, init_loyalty_level)
from bot.moysklad import (find_agent_by_phone, fetch_shipments, fetch_demand_full, apply_discount)
from bot.moysklad import MS_BASE, HEADERS
from bot.formatting import fmt_money, fmt_date_local, render_positions
from bot.accrual import doc_age_seconds, accrue_for_demand
from bot.loyalty import get_redeem_cap, format_level_status, format_level_benefits
from bot.analytics import (
    get_client_statistics, get_client_ranking, get_bonus_history,
    format_client_statistics, format_client_ranking, format_bonus_history
)
from bot.maintenance import (
    get_all_maintenance_status, format_maintenance_summary, format_maintenance_status,
    add_manual_maintenance, MAINTENANCE_WORKS
)

# Настройка логирования
log = logging.getLogger(__name__)

# UUID атрибутов МойСклад
COMPANY_ID = 902665
VIN_ATTR_ID   = "9622737b-b47d-11ee-0a80-066f0015f528"
BRAND_ATTR_ID = "a308e9de-b47d-11ee-0a80-0d3b0016ecc6"
ODO_ATTR_ID   = "58075519-b48a-11ee-0a80-052a0018b89c"
REC_ATTR_ID   = "845f0de1-b4a6-11ee-0a80-103900016c42"

class Auth(StatesGroup):
    wait_name = State()

# ─────────────────────────── клавиатуры ────────────────────────────
# Используем новое премиальное меню
MAIN_MENU_KB = main_menu_premium()

def confirm_redeem_kb() -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения списания бонусов"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить списание", callback_data="redeem_confirm")
    kb.button(text="❌ Отмена", callback_data="redeem_cancel")
    kb.adjust(1)
    return kb.as_markup()

def list_visits_kb(rows: list[dict]) -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for d in rows:
        kb.button(
            text=f"Чек №{d.get('name') or d['id'][:8]} · {fmt_date_local(d['moment'])}",
            callback_data=f"visit_{d['id']}",
        )
    kb.button(text="◀️ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()


def visit_detail_kb() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ К списку", callback_data="back_history")
    kb.button(text="🏠 Главное меню", callback_data="back_main")
    kb.adjust(2)
    return kb.as_markup()

# ─────────────────────────── регистр хендлеров ──────────────────────

def register(dp):

    # /start
    @dp.message(CommandStart())
    async def cmd_start(m: types.Message):
        aid = get_agent_id(m.from_user.id)
        if aid:
            # Пользователь уже авторизован - показываем главное меню
            message = (
                "🎉 Добро пожаловать в систему лояльности!\n\n"
                "✅ Вы авторизованы и можете пользоваться системой.\n\n"
                "Выберите действие:"
            )
            return await m.answer(
                message,
                reply_markup=mini_app_menu_kb()
            )
            
        # Новый пользователь - авторизация
        kb = ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await m.answer(
            "👋 Добро пожаловать в бонусную программу!\n\n"
            "🌟 Для начала работы поделитесь номером телефона:",
            reply_markup=kb
        )

    # контактный номер
    # ─────────────────────────── контакт (авторизация) ───────────────────────────
    @dp.message(F.content_type == ContentType.CONTACT)
    async def contact(m: types.Message, state: FSMContext):
        phone = m.contact.phone_number
        aid   = find_agent_by_phone(phone)

        # ─── клиент уже есть в МойСклад ─────────────────────────────────────────
        if aid:
            register_mapping(
                tg_id   = m.from_user.id,
                agent_id= aid,
                phone   = phone,
                fullname= m.contact.first_name or ""
            )

            # начислим бонусы, если пропустили последнюю отгрузку
            last = fetch_shipments(aid, limit=1)
            if last:
                did = last[0]["id"]
                already = conn.execute(
                    "SELECT 1 FROM accrual_log WHERE demand_id=?", (did,)
                ).fetchone()
                if not already:
                    full = fetch_demand_full(did)
                    if doc_age_seconds(full["moment"]) >= 300:
                        added = accrue_for_demand(full)
                        if added:
                            conn.execute(
                                "INSERT INTO accrual_log(demand_id) VALUES(?)", (did,)
                            )
                            conn.commit()
                            await m.answer(
                                f"✅ Начислено за последнее посещение: {fmt_money(added)}"
                            )

        await m.answer("✅ Вы авторизованы.\nВыберите действие:",
                    reply_markup=mini_app_menu_kb())
        return

        # ─── новый клиент: спрашиваем ФИО и сохраняем номер в FSM ──────────────
        await state.set_state(Auth.wait_name)
        await state.update_data(phone=phone)          # сохраняем номер
        await m.answer("Как к вам обращаться? (ФИО)")


    # ─────────────────────── получили ФИО ───────────────────────────────────────
    @dp.message(Auth.wait_name)
    async def got_name(m: types.Message, state: FSMContext):
        data  = await state.get_data()
        phone = data["phone"]
        name  = m.text.strip()

        # ───── пробуем создать контрагента в МойСклад ─────
        try:
            payload = {
                "name":  name,
                "phone": phone,          # отображается в веб-интерфейсе
                "phones": [              # остаётся и в массиве phones
                    {"phone": phone}
                ]
            }
            resp = requests.post(
                f"{MS_BASE}/counterparty",
                headers=HEADERS,
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()      # ↑ выбросит исключение, если не 2xx
            aid = resp.json()["id"]      # id созданного контрагента

        except Exception as e:
            await m.answer(f"❌ Не удалось создать клиента: {e}")
            return

        # сохраняем связь TG ↔ контрагент + контакты
        register_mapping(m.from_user.id, aid, phone, name)

        # Сообщение о начислении приветственных бонусов
        await m.answer("✅ Вам начислено 100 приветственных бонусов!")

        await state.clear()

        await m.answer(
            "✅ Клиент создан и авторизован.\nВыберите действие:",
            reply_markup=MAIN_MENU_KB
        )


    # ─────────── «Записаться»  →  ШАГ 1: услуга ───────────
    @dp.message(F.text.in_(["📅 Записаться", "Записаться"]))
    async def msg_booking_start(m: types.Message):
        try:
            resp = services(COMPANY_ID)
            services_list = resp["services"] if "services" in resp else resp["data"]["services"]
        except Exception as e:
            return await m.answer(f"Ошибка получения списка услуг: {e}")

        kb = InlineKeyboardBuilder()
        for svc in services_list:
            kb.button(text=svc["title"], callback_data=f"bk_srv_{svc['id']}")   # bk_srv_<srv>
        kb.button(text="◀️ Назад", callback_data="back_menu")
        kb.adjust(1)
        await m.answer("Выберите услугу:", reply_markup=kb.as_markup())


    # ─────────── ШАГ 2: мастер ───────────
  
    @dp.callback_query(F.data.startswith("bk_srv_"))
    async def cb_choose_staff(cq: types.CallbackQuery):
        """После выбора услуги показываем доступных мастеров."""
        await cq.answer()
        srv_id = int(cq.data.split("_")[2])               # bk_srv_<srv_id>

        # --- запрашиваем мастеров в YCLIENTS ---
        try:
            raw = staff(COMPANY_ID, [srv_id])             # <— ваш вызов к API
            # API может вернуть либо список, либо словарь с ключами data/staff
            if isinstance(raw, list):
                staff_list = raw
            elif isinstance(raw, dict):
                staff_list = (
                    raw.get("staff") or                   # { staff:[...] }
                    raw.get("data", {}).get("staff") or   # { data:{ staff:[...] } }
                    raw.get("data") or []                 # { data:[...] }
                )
            else:
                raise TypeError(f"Неожиданный формат: {type(raw)}")
        except Exception as e:
            return await cq.message.answer(f"Ошибка получения сотрудников: {e}")

        if not staff_list:
            return await cq.message.answer("Нет доступных мастеров для этой услуги 😔")

        # --- строим клавиатуру мастеров ---
        kb = InlineKeyboardBuilder()
        for st in staff_list:
            # пропустим всё, что не похоже на словарь сотрудника
            if not isinstance(st, dict):
                continue
            kb.button(
                text=st.get("name", "—"),
                callback_data=f"bk_stf_{srv_id}_{st['id']}"   # bk_stf_<srv_id>_<stf_id>
            )
        kb.button(text="◀️ Назад", callback_data="back_menu")
        kb.adjust(1)

        await cq.message.edit_text("Выберите специалиста:", reply_markup=kb.as_markup())



    # ─────────── ШАГ 3: дата (7 ближайших дней) ───────────
    @dp.callback_query(F.data.startswith("bk_stf_"))
    async def cb_choose_day(cq: types.CallbackQuery):
        await cq.answer()
        _, _, srv_id, stf_id = cq.data.split("_", 3)
        srv_id, stf_id = int(srv_id), int(stf_id)

        today = date.today()
        dates_resp = book_dates(
            COMPANY_ID,
            service_ids=[srv_id],
            staff_id=stf_id,
            date_from=today.isoformat(),
            date_to=(today + timedelta(days=7)).isoformat(),
        )
        dates = dates_resp.get("booking_dates") or dates_resp.get("data", {}).get("booking_dates", [])

        if not dates:
            return await cq.answer("Ближайших слотов нет 😔", show_alert=True)

        kb = InlineKeyboardBuilder()
        for d in dates:
            formatted_date = format_date_russian(d)
            kb.button(
                text=formatted_date,
                callback_data=f"bk_day_{srv_id}_{stf_id}_{d}",
            )
        kb.button(text="◀️ Назад", callback_data=f"bk_srv_{srv_id}")
        kb.adjust(2)
        await cq.message.edit_text("Выберите дату:", reply_markup=kb.as_markup())


    # ─────────── ШАГ 4: время ───────────
    @dp.callback_query(F.data.startswith("bk_day_"))
    async def cb_choose_time(cq: types.CallbackQuery):
        await cq.answer()
        _, _, srv_id, stf_id, day = cq.data.split("_", 4)
        srv_id, stf_id = int(srv_id), int(stf_id)

        try:
            slots = free_slots(COMPANY_ID, stf_id, srv_id, day)
        except Exception as e:
            return await cq.message.answer(f"Ошибка получения времени: {e}")

        if not slots:
            return await cq.answer("На этот день свободного времени нет", show_alert=True)

        kb = InlineKeyboardBuilder()
        for s in slots:
            kb.button(
                text=s["time"],
                callback_data=f"bk_tm_{srv_id}_{stf_id}_{day}_{s['datetime']}",
            )
        kb.button(text="◀️ Назад", callback_data=f"bk_stf_{srv_id}_{stf_id}")
        kb.adjust(3)
        await cq.message.edit_text("Выберите время:", reply_markup=kb.as_markup())


    # ─────────── ШАГ 5: подтверждение ───────────
    @dp.callback_query(F.data.startswith("bk_tm_"))
    async def cb_confirm_record(cq: types.CallbackQuery):
        await cq.answer()
        _, _, srv_id, stf_id, day, iso_dt = cq.data.split("_", 5)
        srv_id, stf_id = int(srv_id), int(stf_id)

        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Подтвердить", callback_data=f"bk_ok_{srv_id}_{stf_id}_{iso_dt}")
        kb.button(text="◀️ Назад", callback_data=f"bk_day_{srv_id}_{stf_id}_{day}")
        kb.adjust(1)

        await cq.message.edit_text(
            f"<b>Проверьте запись</b>\n"
            f"Услуга ID: {srv_id}\n"
            f"Мастер ID: {stf_id}\n"
            f"Дата: {day}\n"
            f"Время: {iso_dt[11:16]}",
            reply_markup=kb.as_markup(),
        )


    # ─────────── ШАГ 6: создание записи ───────────
    @dp.callback_query(F.data.startswith("bk_ok_"))
    async def cb_make_record(cq: types.CallbackQuery, state: FSMContext):
        await cq.answer()
        _, _, srv_id, stf_id, iso_dt = cq.data.split("_", 4)
        srv_id, stf_id = int(srv_id), int(stf_id)

        phone, fullname = user_contact(cq.from_user.id)

        try:
            create_record(
                COMPANY_ID,
                phone=phone,
                fullname=fullname or "Клиент Telegram",
                email="",
                appointments=[
                    {
                        "id": 1,
                        "services": [srv_id],
                        "staff_id": stf_id,
                        "datetime": iso_dt,
                    }
                ],
            )
            await cq.message.edit_text("🎉 Запись успешно создана!")
        except Exception as e:
            await cq.message.edit_text(f"Не удалось создать запись: {e}")



    # баланс (обновленная версия с премиальными иконками)
    @dp.message(F.text.in_(["💎 Баланс", "Баланс"]))
    async def msg_balance(m: types.Message):
        aid = get_agent_id(m.from_user.id)
        if not aid:
            return await m.answer("Сначала выполните /start")
        
        # Получаем баланс и уровень лояльности
        balance = get_balance(aid)
        loyalty_data = get_loyalty_level(aid)
        
        # Используем новую расширенную клавиатуру баланса
        kb = balance_detail_kb()
        
        message = (
            f"💰 <b>Ваш бонусный счёт: {fmt_money(balance)}</b>\n\n"
            f"{format_level_status(loyalty_data['level_id'], loyalty_data['total_spent'])}"
        )
        
        await m.answer(
            message,
            reply_markup=kb,
            parse_mode="HTML"
        )

    @dp.message(F.text.in_(["🎁 Списать баллы", "Списать баллы"]))
    async def msg_redeem_prompt(m: types.Message, state: FSMContext):
        aid = get_agent_id(m.from_user.id)
        if not aid:
            kb = ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Поделиться номером", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            return await m.answer(
                "⚠️ Для списания баллов необходима авторизация.\n"
                "Пожалуйста, поделитесь номером телефона:",
                reply_markup=kb
            )

        # Get current balance
        balance = get_balance(aid)
        if balance == 0:
            return await m.answer(
                "❌ На вашем счёте нет доступных баллов",
                reply_markup=MAIN_MENU_KB
            )

        # Get last visit
        visits = fetch_shipments(aid, limit=1)
        if not visits:
            return await m.answer(
                "❌ История посещений пуста",
                reply_markup=MAIN_MENU_KB
            )

        # Calculate available bonus amount based on loyalty level
        check = fetch_demand_full(visits[0]["id"])
        loyalty_data = get_loyalty_level(aid)
        redeem_cap = get_redeem_cap(loyalty_data["level_id"])
        max_kop = int(check["sum"] * redeem_cap)
        kop = min(balance, max_kop)

        message = (
            f"<b>💳 Списание бонусов</b>\n\n"
            f"💰 Текущий баланс: <b>{fmt_money(balance)}</b>\n"
            f"🧾 Чек №{check.get('name') or check['id'][:8]}\n"
            f"💵 Сумма чека: <b>{fmt_money(check['sum'])}</b>\n"
            f"✨ Доступно к списанию: <b>{fmt_money(kop)}</b>\n"
            f"ℹ️ Можно списать не более {redeem_cap*100:.0f}% от суммы чека\n\n"
            f"Подтвердить списание <b>{fmt_money(kop)}</b>?"
        )

        # Store redemption data in FSM
        await state.update_data(
            check_id=check["id"],
            amount=kop
        )

        await m.answer(
            message,
            reply_markup=confirm_redeem_kb(),
            parse_mode="HTML"
        )

    async def process_redeem(m: types.Message, rub_requested: int | None):
        aid = get_agent_id(m.from_user.id)
        if not aid:
            return await m.answer("Сначала выполните /start")
        bal_kop = get_balance(aid)
        if bal_kop == 0:
            return await m.answer("На счёте нет баллов.")

        visits = fetch_shipments(aid, limit=1)
        if not visits:
            return await m.answer("История пуста.")
        check = fetch_demand_full(visits[0]["id"])
        max_kop = int(check["sum"] * REDEEM_CAP)
        kop = min(bal_kop, max_kop, (rub_requested or max_kop) * 100)
        if kop == 0:
            return await m.answer(
                f"Доступно к списанию: {fmt_money(max_kop)}. Баланс: {fmt_money(bal_kop)}."
            )

        percent = round(kop / check["sum"] * 100, 2)
        apply_discount(check["id"], percent, check["positions"]["rows"])
        change_balance(aid, -kop)
        await m.answer(
            f"Списано {fmt_money(kop)} (≈{percent}% от чека).\n"
            f"Баланс: {fmt_money(bal_kop - kop)}",
            reply_markup=MAIN_MENU_KB,
        )

    @dp.callback_query(F.data == "redeem_confirm")
    async def cb_redeem_confirm(cq: types.CallbackQuery, state: FSMContext):
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return

        data = await state.get_data()
        amount = data.get("amount", 0)
        check_id = data.get("check_id")

        if not amount or not check_id:
            await cq.answer("❌ Ошибка данных", show_alert=True)
            return

        try:
            # Apply discount and update balance
            check = fetch_demand_full(check_id)
            percent = round(amount / check["sum"] * 100, 2)
            apply_discount(check_id, percent, check["positions"]["rows"])
            change_balance(aid, -amount)
            
            # Записываем транзакцию списания
            from bot.db import add_bonus_transaction
            description = f"Списание по чеку №{check.get('name', check['id'][:8])}"
            add_bonus_transaction(aid, "redemption", amount, description, check_id)

            await cq.message.edit_text(
                f"✅ Списано {fmt_money(amount)} (≈{percent}% от чека)\n"
                f"💰 Новый баланс: {fmt_money(get_balance(aid))}",
                reply_markup=None
            )
        except Exception as e:
            await cq.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

    @dp.callback_query(F.data == "redeem_cancel")
    async def cb_redeem_cancel(cq: types.CallbackQuery):
        await cq.answer("Списание отменено")
        await cq.message.edit_text(
            "❌ Списание отменено",
            reply_markup=None
        )

    # история (обновленная версия)
    @dp.message(F.text.in_(["📊 История", "История посещений"]))
    async def msg_history(m: types.Message):
        aid = get_agent_id(m.from_user.id)
        if not aid:
            return await m.answer(
                "⚠️ Для просмотра истории необходима авторизация.\n"
                "Пожалуйста, выполните /start"
            )

        visits = fetch_shipments(aid, limit=20)
        if not visits:
            return await m.answer(
                "📝 История посещений пока пуста",
                reply_markup=MAIN_MENU_KB
            )

        await m.answer(
            "📋 Выберите визит для просмотра деталей:",
            reply_markup=list_visits_kb(visits)
        )

    # просмотр чека
    @dp.callback_query(lambda c: c.data.startswith("visit_"))
    async def cb_visit(callback: types.CallbackQuery):
        vid = callback.data.replace("visit_", "")
        try:
            v = fetch_demand_full(vid)
            if not v:
                await callback.message.edit_text(
                    "❌ Отгрузка не найдена или была удалена",
                    reply_markup=None
                )
                return

            # Получаем атрибуты из отгрузки
            attributes = v.get('attributes', {})
            car_model = next((attr['value'] for attr in attributes if attr['name'] == 'Марка/модель'), 'Не указано')
            mileage = next((attr['value'] for attr in attributes if attr['name'] == 'Пробег'), 'Не указано')
            vin = next((attr['value'] for attr in attributes if attr['name'] == 'VIN'), 'Не указано')
            recommendations = next((attr['value'] for attr in attributes if attr['name'] == 'Рекомендации'), 'Нет рекомендаций')

            text = (
                f"📋 Чек №{v.get('name') or v['id'][:8]}\n"
                f"📅 {fmt_date_local(v['moment'])}\n"
                f"💰 Сумма: {fmt_money(v['sum'])}\n\n"
                f"🚗 Автомобиль: {car_model}\n"
                f"📍 Пробег: {mileage}\n"
                f"🔢 VIN: {vin}\n\n"
                f"📝 Выполненные работы:\n"
                f"{render_positions(v.get('positions', {}).get('rows', []))}\n\n"
                f"💡 Рекомендации:\n{recommendations}"
            )
            
            await callback.message.edit_text(text, parse_mode="HTML")
            
        except Exception as e:
            log.error(f"Ошибка при получении деталей отгрузки: {e}")
            await callback.message.edit_text(
                "❌ Не удалось загрузить детали отгрузки",
                reply_markup=None
            )

    # назад: из карточки в список
    @dp.callback_query(F.data == "back_history")
    async def cb_back_history(cq: types.CallbackQuery):
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            return await cq.answer()
        visits = fetch_shipments(aid, limit=20)
        if not visits:
            return await cq.answer("История пуста.", show_alert=True)
        await cq.message.edit_text("Недавние посещения:", reply_markup=list_visits_kb(visits))
        await cq.answer()

    # показать статус лояльности
    @dp.callback_query(F.data == "show_status")
    async def cb_show_status(cq: types.CallbackQuery):
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        loyalty_data = get_loyalty_level(aid)
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад к балансу", callback_data="back_to_balance")
        kb.adjust(1)
        
        message = (
            f"📊 <b>Детальная информация о статусе</b>\n\n"
            f"{format_level_status(loyalty_data['level_id'], loyalty_data['total_spent'])}"
        )
        
        await cq.message.edit_text(
            message,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    # показать привилегии
    @dp.callback_query(F.data == "show_benefits")
    async def cb_show_benefits(cq: types.CallbackQuery):
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        loyalty_data = get_loyalty_level(aid)
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад к балансу", callback_data="back_to_balance")
        kb.adjust(1)
        
        message = format_level_benefits(loyalty_data['level_id'])
        
        await cq.message.edit_text(
            message,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    # назад к балансу
    @dp.callback_query(F.data == "back_to_balance")
    async def cb_back_to_balance(cq: types.CallbackQuery):
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        # Получаем баланс и уровень лояльности
        balance = get_balance(aid)
        loyalty_data = get_loyalty_level(aid)
        
        # Создаем клавиатуру с дополнительными опциями
        kb = InlineKeyboardBuilder()
        kb.button(text="📊 Мой статус", callback_data="show_status")
        kb.button(text="🎁 Привилегии", callback_data="show_benefits")
        kb.adjust(2)
        
        message = (
            f"💰 <b>Ваш бонусный счёт: {fmt_money(balance)}</b>\n\n"
            f"{format_level_status(loyalty_data['level_id'], loyalty_data['total_spent'])}"
        )
        
        await cq.message.edit_text(
            message,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    # Новые обработчики для расширенной клавиатуры баланса
    @dp.callback_query(F.data == "show_transactions")
    async def cb_show_transactions(cq: types.CallbackQuery):
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        try:
            # Получаем последние 10 транзакций
            transactions = conn.execute("""
                SELECT operation_type, amount, description, created_at 
                FROM bonus_transactions 
                WHERE agent_id = ? 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (aid,)).fetchall()
            
            if not transactions:
                message = "📝 <b>История операций</b>\n\nПока нет операций"
            else:
                message = "📝 <b>История операций</b>\n\n"
                for tx in transactions:
                    op_type, amount, desc, created_at = tx
                    date = datetime.fromisoformat(created_at).strftime("%d.%m.%Y %H:%M")
                    icon = "➕" if op_type == "accrual" else "➖"
                    message += f"{icon} {fmt_money(amount)} - {desc}\n<i>{date}</i>\n\n"
            
            kb = InlineKeyboardBuilder()
            kb.button(text="◀️ Назад к балансу", callback_data="back_to_balance")
            kb.adjust(1)
            
            await cq.message.edit_text(
                message,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Ошибка при получении истории транзакций: {e}")
            await cq.answer("❌ Ошибка при загрузке истории", show_alert=True)
        
        await cq.answer()
    
    @dp.callback_query(F.data == "show_achievements")
    async def cb_show_achievements(cq: types.CallbackQuery):
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        loyalty_data = get_loyalty_level(aid)
        visits = fetch_shipments(aid, limit=100)  # Получаем больше данных
        
        # Подсчитываем достижения
        total_visits = len(visits)
        current_year_visits = len([v for v in visits if datetime.fromisoformat(v['moment'].replace('Z', '+00:00')).year == datetime.now().year])
        
        achievements = []
        if total_visits >= 1:
            achievements.append("🎉 Первое посещение")
        if total_visits >= 5:
            achievements.append("🎆 5 посещений")
        if total_visits >= 10:
            achievements.append("🏆 10 посещений")
        if loyalty_data['level_id'] != 'Bronze':
            achievements.append(f"🌟 Статус {loyalty_data['level_id']}")
        if loyalty_data['total_spent'] >= 100000:
            achievements.append("💰 Потратил 100,000+ руб")
        
        message = "🏆 <b>Ваши достижения</b>\n\n"
        
        if achievements:
            for achievement in achievements:
                message += f"✅ {achievement}\n"
        else:
            message += "🙌 Пока нет достижений\nПродолжайте пользоваться нашими услугами!"
        
        message += f"\n\n📊 Статистика:\n• Всего посещений: {total_visits}\n• В этом году: {current_year_visits}"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад к балансу", callback_data="back_to_balance")
        kb.adjust(1)
        
        await cq.message.edit_text(
            message,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()

    # Профиль (расширенная версия)
    @dp.message(F.text == "👤 Профиль")
    async def msg_profile(m: types.Message):
        aid = get_agent_id(m.from_user.id)
        if not aid:
            return await m.answer("Сначала выполните /start")

        # Получаем подробную информацию о профиле
        balance = get_balance(aid)
        loyalty_data = get_loyalty_level(aid)
        
        # Получаем контактную информацию
        phone, fullname = user_contact(m.from_user.id)
        
        profile_info = (
            f"👤 <b>Личный кабинет</b>\n\n"
            f"👋 Имя: <b>{fullname or 'Не указано'}</b>\n"
            f"📞 Телефон: <b>{phone or 'Не указан'}</b>\n\n"
            f"💎 Баланс: <b>{fmt_money(balance)}</b>\n"
            f"🏆 Статус: <b>{loyalty_data['level_id']}</b>\n"
            f"💰 Потрачено всего: <b>{fmt_money(loyalty_data['total_spent'])}</b>\n\n"
            f"Выберите действие:"
        )

        await m.answer(
            profile_info, 
            reply_markup=profile_menu_kb(),
            parse_mode="HTML"
        )

    # Поддержка (расширенная версия)
    @dp.message(F.text == "💬 Поддержка")
    async def msg_support(m: types.Message):
        support_text = (
            "💬 <b>Центр поддержки</b>\n\n"
            "Мы готовы помочь вам с любыми вопросами!\n\n"
            "Выберите подходящий раздел:"
        )
        await m.answer(
            support_text, 
            reply_markup=support_menu_kb(),
            parse_mode="HTML"
        )
    
    # Обработчики callback-запросов для профиля
    @dp.callback_query(F.data == "profile_edit")
    async def cb_profile_edit(cq: types.CallbackQuery):
        await cq.answer("🚧 Функция редактирования профиля находится в разработке", show_alert=True)
    
    @dp.callback_query(F.data == "profile_notifications")
    async def cb_profile_notifications(cq: types.CallbackQuery):
        await cq.answer("🚧 Настройки уведомлений находятся в разработке", show_alert=True)
    
    @dp.callback_query(F.data == "profile_cars")
    async def cb_profile_cars(cq: types.CallbackQuery):
        await cq.answer("🚧 Управление автомобилями находится в разработке", show_alert=True)
    
    @dp.callback_query(F.data == "profile_contacts")
    async def cb_profile_contacts(cq: types.CallbackQuery):
        phone, fullname = user_contact(cq.from_user.id)
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад к профилю", callback_data="back_to_profile")
        kb.adjust(1)
        
        message = (
            f"📞 <b>Контактная информация</b>\n\n"
            f"👤 Имя: <b>{fullname or 'Не указано'}</b>\n"
            f"📱 Телефон: <b>{phone or 'Не указан'}</b>\n"
            f"💬 Telegram: <b>@{cq.from_user.username or 'не указан'}</b>\n\n"
            f"Для изменения данных обратитесь к администратору."
        )
        
        await cq.message.edit_text(
            message,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    @dp.callback_query(F.data == "profile_settings")
    async def cb_profile_settings(cq: types.CallbackQuery):
        await cq.answer("⚙️ Настройки профиля находятся в разработке", show_alert=True)
    
    @dp.callback_query(F.data == "back_to_profile")
    async def cb_back_to_profile(cq: types.CallbackQuery):
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        balance = get_balance(aid)
        loyalty_data = get_loyalty_level(aid)
        phone, fullname = user_contact(cq.from_user.id)
        
        profile_info = (
            f"👤 <b>Личный кабинет</b>\n\n"
            f"👋 Имя: <b>{fullname or 'Не указано'}</b>\n"
            f"📞 Телефон: <b>{phone or 'Не указан'}</b>\n\n"
            f"💎 Баланс: <b>{fmt_money(balance)}</b>\n"
            f"🏆 Статус: <b>{loyalty_data['level_id']}</b>\n"
            f"💰 Потрачено всего: <b>{fmt_money(loyalty_data['total_spent'])}</b>\n\n"
            f"Выберите действие:"
        )
        
        await cq.message.edit_text(
            profile_info,
            reply_markup=profile_menu_kb(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    # Обработчики callback-запросов для поддержки
    @dp.callback_query(F.data == "support_faq")
    async def cb_support_faq(cq: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад к поддержке", callback_data="back_to_support")
        kb.adjust(1)
        
        faq_text = (
            "❓ <b>Часто задаваемые вопросы</b>\n\n"
            "<b>Q: Как накапливаются бонусы?</b>\n"
            "A: Бонусы начисляются автоматически после каждого обслуживания в зависимости от вашего статуса лояльности.\n\n"
            "<b>Q: Как потратить бонусы?</b>\n"
            "A: Используйте кнопку '🎁 Списать баллы' для применения бонусов к последнему чеку.\n\n"
            "<b>Q: Как отслеживать ТО?</b>\n"
            "A: Используйте раздел '🔧 ТО' для просмотра статуса всех работ по техническому обслуживанию.\n\n"
            "<b>Q: Можно ли добавить информацию о ТО вручную?</b>\n"
            "A: Да, в разделе ТО есть функция добавления записей вручную."
        )
        
        await cq.message.edit_text(
            faq_text,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    @dp.callback_query(F.data == "support_contact")
    async def cb_support_contact(cq: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад к поддержке", callback_data="back_to_support")
        kb.adjust(1)
        
        contact_text = (
            "📞 <b>Связаться с нами</b>\n\n"
            "📍 Адрес: г. Москва, ул. Примерная, 123\n"
            "📱 Телефон: +7 (123) 456-78-90\n"
            "📧 Email: support@example.com\n"
            "🕐 Режим работы: Пн-Пт 9:00-18:00\n\n"
            "Мы всегда готовы помочь вам!"
        )
        
        await cq.message.edit_text(
            contact_text,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    @dp.callback_query(F.data == "support_guide")
    async def cb_support_guide(cq: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ Назад к поддержке", callback_data="back_to_support")
        kb.adjust(1)
        
        guide_text = (
            "📋 <b>Руководство пользователя</b>\n\n"
            "💎 <b>Баланс</b> - просмотр текущих бонусов и статуса лояльности\n"
            "🎁 <b>Списать баллы</b> - использование бонусов для оплаты\n"
            "📊 <b>История</b> - все ваши посещения и транзакции\n"
            "📈 <b>Аналитика</b> - статистика и рейтинги\n"
            "🔧 <b>ТО</b> - управление техническим обслуживанием\n"
            "📅 <b>Записаться</b> - онлайн-запись на обслуживание\n"
            "👤 <b>Профиль</b> - управление личными данными\n"
            "💬 <b>Поддержка</b> - помощь и информация\n\n"
            "Нажимайте на кнопки для доступа к функциям!"
        )
        
        await cq.message.edit_text(
            guide_text,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    @dp.callback_query(F.data == "support_feedback")
    async def cb_support_feedback(cq: types.CallbackQuery):
        await cq.answer("💡 Функция отправки предложений находится в разработке", show_alert=True)
    
    @dp.callback_query(F.data == "back_to_support")
    async def cb_back_to_support(cq: types.CallbackQuery):
        support_text = (
            "💬 <b>Центр поддержки</b>\n\n"
            "Мы готовы помочь вам с любыми вопросами!\n\n"
            "Выберите подходящий раздел:"
        )
        
        await cq.message.edit_text(
            support_text,
            reply_markup=support_menu_kb(),
            parse_mode="HTML"
        )
        await cq.answer()

    # ─────────────────────────── АНАЛИТИКА ─────────────────────────────
    
    @dp.message(F.text.in_(["📈 Аналитика", "Аналитика"]))
    async def msg_analytics(m: types.Message):
        """Главное меню аналитики"""
        aid = get_agent_id(m.from_user.id)
        if not aid:
            return await m.answer(
                "⚠️ Для просмотра аналитики необходима авторизация.\n"
                "Пожалуйста, выполните /start"
            )
        
        kb = InlineKeyboardBuilder()
        kb.button(text="📊 Моя статистика", callback_data="analytics_stats")
        kb.button(text="🏆 Мой рейтинг", callback_data="analytics_ranking")
        kb.button(text="📝 История бонусов", callback_data="analytics_history")
        kb.button(text="◀️ Назад", callback_data="back_main")
        kb.adjust(1)
        
        await m.answer(
            "📈 <b>Аналитика и отчеты</b>\n\n"
            "Выберите интересующий раздел:",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
    
    @dp.callback_query(F.data == "analytics_stats")
    async def cb_analytics_stats(cq: types.CallbackQuery):
        """Показать статистику клиента"""
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        await cq.message.edit_text("⏳ Загрузка статистики...")
        
        try:
            stats = get_client_statistics(aid)
            message = format_client_statistics(stats)
            
            kb = InlineKeyboardBuilder()
            kb.button(text="◀️ Назад к аналитике", callback_data="back_analytics")
            kb.adjust(1)
            
            await cq.message.edit_text(
                message,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Ошибка при получении статистики: {e}")
            await cq.message.edit_text(
                "❌ Ошибка при загрузке статистики",
                reply_markup=None
            )
        
        await cq.answer()
    
    @dp.callback_query(F.data == "analytics_ranking")
    async def cb_analytics_ranking(cq: types.CallbackQuery):
        """Показать рейтинг клиента"""
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        await cq.message.edit_text("⏳ Загрузка рейтинга...")
        
        try:
            ranking = get_client_ranking(aid)
            message = format_client_ranking(ranking, aid)
            
            kb = InlineKeyboardBuilder()
            kb.button(text="◀️ Назад к аналитике", callback_data="back_analytics")
            kb.adjust(1)
            
            await cq.message.edit_text(
                message,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Ошибка при получении рейтинга: {e}")
            await cq.message.edit_text(
                "❌ Ошибка при загрузке рейтинга",
                reply_markup=None
            )
        
        await cq.answer()
    
    @dp.callback_query(F.data == "analytics_history")
    async def cb_analytics_history(cq: types.CallbackQuery):
        """Показать историю бонусов"""
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        await cq.message.edit_text("⏳ Загрузка истории...")
        
        try:
            history = get_bonus_history(aid)
            message = format_bonus_history(history)
            
            kb = InlineKeyboardBuilder()
            kb.button(text="◀️ Назад к аналитике", callback_data="back_analytics")
            kb.adjust(1)
            
            await cq.message.edit_text(
                message,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Ошибка при получении истории: {e}")
            await cq.message.edit_text(
                "❌ Ошибка при загрузке истории",
                reply_markup=None
            )
        
        await cq.answer()
    
    @dp.callback_query(F.data == "back_analytics")
    async def cb_back_analytics(cq: types.CallbackQuery):
        """Вернуться в меню аналитики"""
        kb = InlineKeyboardBuilder()
        kb.button(text="📊 Моя статистика", callback_data="analytics_stats")
        kb.button(text="🏆 Мой рейтинг", callback_data="analytics_ranking")
        kb.button(text="📝 История бонусов", callback_data="analytics_history")
        kb.button(text="◀️ Назад", callback_data="back_main")
        kb.adjust(1)
        
        await cq.message.edit_text(
            "📈 <b>Аналитика и отчеты</b>\n\n"
            "Выберите интересующий раздел:",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    # ─────────────────────────── ТЕХНИЧЕСКОЕ ОБСЛУЖИВАНИЕ ─────────────────────────────
    
    @dp.message(F.text == "🔧 ТО")
    async def msg_maintenance(m: types.Message):
        """Главное меню технического обслуживания"""
        aid = get_agent_id(m.from_user.id)
        if not aid:
            return await m.answer(
                "⚠️ Для просмотра информации о ТО необходима авторизация.\n"
                "Пожалуйста, выполните /start"
            )
        
        await m.answer("⏳ Загрузка данных о техническом обслуживании...")
        
        try:
            statuses = get_all_maintenance_status(aid)
            summary = format_maintenance_summary(statuses)
            
            kb = InlineKeyboardBuilder()
            kb.button(text="📋 Список работ ТО", callback_data="maintenance_list")
            kb.button(text="➕ Добавить запись", callback_data="maintenance_add")
            kb.button(text="📊 Статистика ТО", callback_data="maintenance_stats")
            kb.button(text="◀️ Назад", callback_data="back_main")
            kb.adjust(1)
            
            await m.answer(
                summary,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Ошибка при получении данных ТО: {e}")
            await m.answer(
                "❌ Ошибка при загрузке данных о техническом обслуживании",
                reply_markup=MAIN_MENU_KB
            )
    
    @dp.callback_query(F.data == "maintenance_list")
    async def cb_maintenance_list(cq: types.CallbackQuery):
        """Показать список всех работ ТО"""
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        await cq.message.edit_text("⏳ Загрузка списка работ...")
        
        try:
            statuses = get_all_maintenance_status(aid)
            
            kb = InlineKeyboardBuilder()
            for status in statuses:
                work_id = status["work_id"]
                work_info = status["work_info"]
                
                # Иконка статуса
                if status["status"] == "overdue":
                    status_icon = "🔴"
                elif status["status"] == "soon":
                    status_icon = "🟡"
                elif status["status"] == "never_done":
                    status_icon = "⚪"
                else:
                    status_icon = "🟢"
                
                kb.button(
                    text=f"{status_icon} {work_info['emoji']} {work_info['name'][:25]}...",
                    callback_data=f"maintenance_work_{work_id}"
                )
            
            kb.button(text="◀️ Назад к ТО", callback_data="back_maintenance")
            kb.adjust(1)
            
            await cq.message.edit_text(
                "🔧 <b>Список работ технического обслуживания</b>\n\n"
                "Выберите работу для просмотра деталей:",
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Ошибка при получении списка работ ТО: {e}")
            await cq.answer("❌ Ошибка при загрузке списка", show_alert=True)
        
        await cq.answer()
    
    @dp.callback_query(F.data.startswith("maintenance_work_"))
    async def cb_maintenance_work(cq: types.CallbackQuery):
        """Показать детали конкретной работы ТО"""
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        work_id = int(cq.data.split("_")[2])
        
        try:
            from bot.maintenance import calculate_maintenance_status
            status = calculate_maintenance_status(aid, work_id)
            message = format_maintenance_status(status)
            
            kb = InlineKeyboardBuilder()
            kb.button(text="➕ Добавить запись", callback_data=f"maintenance_add_{work_id}")
            kb.button(text="📋 История", callback_data=f"maintenance_history_{work_id}")
            kb.button(text="◀️ К списку", callback_data="maintenance_list")
            kb.adjust(1)
            
            await cq.message.edit_text(
                message,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Ошибка при получении деталей работы ТО: {e}")
            await cq.answer("❌ Ошибка при загрузке деталей", show_alert=True)
        
        await cq.answer()
    
    class MaintenanceAdd(StatesGroup):
        wait_work = State()
        wait_date = State()
        wait_mileage = State()
        wait_notes = State()
    
    @dp.callback_query(F.data == "maintenance_add")
    async def cb_maintenance_add_start(cq: types.CallbackQuery, state: FSMContext):
        """Начать добавление записи о ТО"""
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        kb = InlineKeyboardBuilder()
        for work_id, work_info in MAINTENANCE_WORKS.items():
            kb.button(
                text=f"{work_info['emoji']} {work_info['name'][:30]}...",
                callback_data=f"maintenance_select_{work_id}"
            )
        kb.button(text="❌ Отмена", callback_data="back_maintenance")
        kb.adjust(1)
        
        await state.set_state(MaintenanceAdd.wait_work)
        await cq.message.edit_text(
            "➕ <b>Добавление записи о ТО</b>\n\n"
            "Выберите тип выполненной работы:",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    @dp.callback_query(F.data.startswith("maintenance_select_"))
    async def cb_maintenance_select_work(cq: types.CallbackQuery, state: FSMContext):
        """Выбрана работа, запрашиваем дату"""
        work_id = int(cq.data.split("_")[2])
        work_info = MAINTENANCE_WORKS[work_id]
        
        await state.update_data(work_id=work_id)
        await state.set_state(MaintenanceAdd.wait_date)
        
        today = datetime.now().strftime("%d.%m.%Y")
        
        await cq.message.edit_text(
            f"📅 <b>Дата выполнения работы</b>\n\n"
            f"🔧 Работа: {work_info['emoji']} {work_info['name']}\n\n"
            f"Введите дату выполнения в формате ДД.ММ.ГГГГ\n"
            f"Например: {today}",
            reply_markup=None,
            parse_mode="HTML"
        )
        await cq.answer()
    
    @dp.message(MaintenanceAdd.wait_date)
    async def maintenance_got_date(m: types.Message, state: FSMContext):
        """Получена дата, запрашиваем пробег"""
        date_str = m.text.strip()
        
        # Валидация даты
        try:
            parsed_date = datetime.strptime(date_str, "%d.%m.%Y")
            iso_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            await m.answer(
                "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n"
                "Например: 25.12.2024"
            )
            return
        
        await state.update_data(date=iso_date)
        await state.set_state(MaintenanceAdd.wait_mileage)
        
        aid = get_agent_id(m.from_user.id)
        from bot.maintenance import get_current_mileage
        current_mileage = get_current_mileage(aid)
        
        await m.answer(
            f"🛣️ <b>Пробег при выполнении работы</b>\n\n"
            f"Введите пробег в километрах (только цифры)\n"
            f"Текущий пробег: {current_mileage:,} км",
            parse_mode="HTML"
        )
    
    @dp.message(MaintenanceAdd.wait_mileage)
    async def maintenance_got_mileage(m: types.Message, state: FSMContext):
        """Получен пробег, запрашиваем заметки"""
        mileage_str = m.text.strip()
        
        # Валидация пробега
        try:
            mileage = int(''.join(filter(str.isdigit, mileage_str)))
            if mileage <= 0:
                raise ValueError()
        except ValueError:
            await m.answer(
                "❌ Неверный формат пробега. Введите только цифры\n"
                "Например: 50000"
            )
            return
        
        await state.update_data(mileage=mileage)
        await state.set_state(MaintenanceAdd.wait_notes)
        
        kb = InlineKeyboardBuilder()
        kb.button(text="Пропустить", callback_data="maintenance_skip_notes")
        kb.adjust(1)
        
        await m.answer(
            f"📝 <b>Дополнительные заметки</b>\n\n"
            f"Введите дополнительную информацию о выполненной работе\n"
            f"(марка масла, номер детали и т.д.)\n\n"
            f"Или нажмите 'Пропустить'",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
    
    @dp.message(MaintenanceAdd.wait_notes)
    async def maintenance_got_notes(m: types.Message, state: FSMContext):
        """Получены заметки, сохраняем запись"""
        notes = m.text.strip()
        await maintenance_save_record(m, state, notes)
    
    @dp.callback_query(F.data == "maintenance_skip_notes")
    async def cb_maintenance_skip_notes(cq: types.CallbackQuery, state: FSMContext):
        """Пропуск заметок, сохраняем запись"""
        await maintenance_save_record(cq.message, state, "")
        await cq.answer()
    
    async def maintenance_save_record(m: types.Message, state: FSMContext, notes: str):
        """Сохранение записи о ТО"""
        data = await state.get_data()
        aid = get_agent_id(m.from_user.id if hasattr(m, 'from_user') else m.chat.id)
        
        work_id = data["work_id"]
        date = data["date"]
        mileage = data["mileage"]
        
        # Сохраняем запись
        success = add_manual_maintenance(aid, work_id, date, mileage, notes)
        
        await state.clear()
        
        if success:
            work_info = MAINTENANCE_WORKS[work_id]
            await m.answer(
                f"✅ <b>Запись успешно добавлена!</b>\n\n"
                f"🔧 Работа: {work_info['emoji']} {work_info['name']}\n"
                f"📅 Дата: {datetime.fromisoformat(date).strftime('%d.%m.%Y')}\n"
                f"🛣️ Пробег: {mileage:,} км\n"
                f"📝 Заметки: {notes or 'Нет'}\n\n"
                f"Данные сохранены в вашей истории ТО.",
                reply_markup=MAIN_MENU_KB,
                parse_mode="HTML"
            )
        else:
            await m.answer(
                "❌ Ошибка при сохранении записи. Попробуйте снова.",
                reply_markup=MAIN_MENU_KB
            )
    
    @dp.callback_query(F.data.startswith("maintenance_history_"))
    async def cb_maintenance_history(cq: types.CallbackQuery):
        """Показать историю конкретной работы ТО"""
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        work_id = int(cq.data.split("_")[2])
        work_info = MAINTENANCE_WORKS[work_id]
        
        # Получаем историю выполнения этой работы
        history = conn.execute("""
            SELECT performed_date, mileage, source, notes, created_at
            FROM maintenance_history 
            WHERE agent_id = ? AND work_id = ?
            ORDER BY performed_date DESC
            LIMIT 10
        """, (aid, work_id)).fetchall()
        
        if not history:
            text = f"📋 <b>История: {work_info['emoji']} {work_info['name']}</b>\n\nИстория пока пуста"
        else:
            text = f"📋 <b>История: {work_info['emoji']} {work_info['name']}</b>\n\n"
            for i, record in enumerate(history, 1):
                date = datetime.fromisoformat(record[0])
                source_icon = "✋" if record[2] == "manual" else "🔄"
                text += f"{i}. {source_icon} {date.strftime('%d.%m.%Y')} при {record[1]:,} км\n"
                if record[3]:  # есть заметки
                    text += f"   📝 {record[3]}\n"
                text += "\n"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="◀️ К работе", callback_data=f"maintenance_work_{work_id}")
        kb.adjust(1)
        
        await cq.message.edit_text(
            text,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await cq.answer()
    
    @dp.callback_query(F.data == "back_maintenance")
    async def cb_back_maintenance(cq: types.CallbackQuery):
        """Вернуться в главное меню ТО"""
        aid = get_agent_id(cq.from_user.id)
        if not aid:
            await cq.answer("⚠️ Необходима авторизация", show_alert=True)
            return
        
        try:
            statuses = get_all_maintenance_status(aid)
            summary = format_maintenance_summary(statuses)
            
            kb = InlineKeyboardBuilder()
            kb.button(text="📋 Список работ ТО", callback_data="maintenance_list")
            kb.button(text="➕ Добавить запись", callback_data="maintenance_add")
            kb.button(text="📊 Статистика ТО", callback_data="maintenance_stats")
            kb.button(text="◀️ Назад", callback_data="back_main")
            kb.adjust(1)
            
            await cq.message.edit_text(
                summary,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception as e:
            log.error(f"Ошибка при возврате в меню ТО: {e}")
            await cq.answer("❌ Ошибка при загрузке меню", show_alert=True)
        
        await cq.answer()
    
    # Обработчик кнопки "Продолжить в чате"
    @dp.callback_query(F.data == "continue_chat")
    async def cb_continue_chat(cq: types.CallbackQuery):
        """Переход к обычному меню бота"""
        await cq.answer()
        await cq.message.edit_text(
            "📱 Отлично! Вы выбрали работу с ботом в чате.\n\n"
            "🌟 В любой момент вы можете открыть современное приложение \n"
            "через кнопку меню или используя команду /app\n\n"
            "Выберите действие:",
            reply_markup=None
        )
        await cq.message.answer(
            "💎 Добро пожаловать в систему лояльности!\n\n"
            "Используйте меню ниже для управления бонусами и услугами:",
            reply_markup=mini_app_menu_kb()
        )
    
    # Команда для быстрого доступа к Mini App
    @dp.message(F.text == "/app")
    async def cmd_app(m: types.Message):
        """Команда для открытия Mini App"""
        aid = get_agent_id(m.from_user.id)
        if not aid:
            return await m.answer(
                "⚠️ Для доступа к приложению необходима авторизация.\n"
                "Пожалуйста, выполните /start"
            )
        
        message = (
            "🌟 **Современное приложение лояльности**\n\n"
            "✨ В приложении доступно:\n"
            "• Удобный интерфейс для всех функций\n"
            "• Детальная статистика и аналитика\n"
            "• Современный дизайн и анимации\n"
            "• Быстрый доступ ко всем возможностям\n\n"
            "Нажмите кнопку ниже, чтобы открыть:"
        )
        
        kb = InlineKeyboardBuilder()
        kb.button(
            text="🚀 Открыть приложение",
            web_app=types.WebAppInfo(url=MINIAPP_URL)
        )
        kb.adjust(1)
        
        await m.answer(
            message,
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
    
    # Обработчик кнопки "🌟 Приложение" из меню
    @dp.message(F.text.in_(["🌟 Приложение"]))
    async def msg_open_app(m: types.Message):
        """Открытие Mini App из меню"""
        aid = get_agent_id(m.from_user.id)
        if not aid:
            return await m.answer(
                "⚠️ Для доступа к приложению необходима авторизации.\n"
                "Пожалуйста, выполните /start"
            )
        
        message = (
            "🌟 *Приложение системы лояльности*\n\n"
            "✨ Добро пожаловать в современное приложение!\n\n"
            "📱 Здесь доступны все функции:\n"
            "• Просмотр баланса и статистики\n"
            "• История посещений и транзакций\n"
            "• Управление техобслуживанием\n"
            "• Удобная навигация и дизайн\n\n"
            "Нажмите кнопку ниже для продолжения:"
        )
        
        kb = InlineKeyboardBuilder()
        kb.button(
            text="🚀 Открыть приложение",
            web_app=types.WebAppInfo(url=MINIAPP_URL)
        )
        kb.adjust(1)
        
        await m.answer(
            message,
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
    
    # Обработчик callback для webapp_coming_soon
    @dp.callback_query(F.data == "webapp_coming_soon")
    async def cb_webapp_coming_soon(cq: types.CallbackQuery):
        """Уведомление о том, что веб-приложение в разработке"""
        await cq.answer(
            "🚧 Веб-приложение находится в разработке.\n"
            "Скоро будет доступна улучшенная версия!",
            show_alert=True
        )
    
    # назад: главное меню
    @dp.callback_query(F.data == "back_main")
    async def cb_back_main(cq: types.CallbackQuery):
        await cq.message.edit_text("Главное меню", reply_markup=None)
        await cq.message.answer("Выберите действие:", reply_markup=MAIN_MENU_KB)
        await cq.answer()
