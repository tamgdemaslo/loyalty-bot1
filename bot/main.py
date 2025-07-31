# loyalty-bot/bot/main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.handlers import register as register_handlers
# from bot.accrual import accrual_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s: %(message)s",
)

async def main() -> None:
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN is not set. Please check your configuration.")
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register standard handlers
    register_handlers(dp)

    async with bot:
        # Временно отключаем accrual_loop
        # try:
        #     # Background task for bonus accrual
        #     asyncio.create_task(accrual_loop())
        # except Exception as e:
        #     logging.error(f"Error in accrual_loop: {e}")

        # Remove old updates and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
