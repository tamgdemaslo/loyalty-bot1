import os
import pytz
from dotenv import load_dotenv

load_dotenv()

YCLIENTS_PARTNER_ID = 9354
YCLIENTS_PARTNER_TOKEN = os.getenv("YCLIENTS_PARTNER_TOKEN", "mz5bf2yp97nbs4s45e9j")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7914899311:AAGY4CjuMqZX3w1eS7zCM2yNMW3312xCwPE")
MS_TOKEN = os.getenv("MS_TOKEN", "dc5177784c1f4de72a19188ab9e9c567e2cb2916")
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://loyalty-bot1.onrender.com")

if not (BOT_TOKEN and MS_TOKEN):
    raise RuntimeError("Укажите BOT_TOKEN и MS_TOKEN — в .env или переменных окружения!")

# MoySklad
MS_BASE = "https://api.moysklad.ru/api/remap/1.2/entity"
HEADERS = {"Authorization": f"Bearer {MS_TOKEN}", "Accept": "application/json;charset=utf-8"}

# Логика бонусов
BONUS_RATE = 0.05  # 5 %
REDEEM_CAP = 0.30  # можно списать ≤ 30 %
MSK = pytz.timezone("Europe/Moscow")
USER_TZ = pytz.timezone("Europe/Kaliningrad")
