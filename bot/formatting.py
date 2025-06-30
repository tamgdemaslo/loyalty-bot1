from dateutil import parser as dateparser
from .config import MSK, USER_TZ

# ─────────────────────────── даты/деньги ────────────────────────────
def fmt_date_local(iso: str) -> str:
    """Преобразует момент из МойСклада (naive-MSK) в локальное USER_TZ."""
    ts = dateparser.isoparse(iso).replace(tzinfo=MSK)
    return ts.astimezone(USER_TZ).strftime("%d.%m.%Y %H:%M")

def fmt_money(kop: int) -> str:
    rub = kop / 100
    return f"{rub:,.2f} ₽".rstrip("0").rstrip(",")

# ─────────────────────────── позиции ────────────────────────────────
def render_positions(rows: list) -> str:
    """
    Получает d['positions']['rows'] из документа demand и
    возвращает красивый HTML-список вида:
        • Товар — 2 × 450 ₽ = 900 ₽
    """
    lines: list[str] = []
    for p in rows:
        art  = p["assortment"]
        name = art.get("name", "—")
        qty  = p.get("quantity", 1)
        price_kop = p.get("price", 0)
        total_kop = int(price_kop * qty)
        lines.append(
            f"• <b>{name}</b> — {qty:g} × {fmt_money(price_kop)} = {fmt_money(total_kop)}"
        )
    return "\n".join(lines)
