import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from bot.handlers.subs_list import router as list_subs_router
from bot.handlers.stats import router as stats_router
from bot.handlers.add_sub import router as add_sub_router
from bot.config import config
from bot.database.db import init_db
from bot.handlers.start import router as start_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.services.scheduler import NotificationScheduler

async def setup_bot_metadata(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Главное меню / Перезапуск"),
    ]
    await bot.set_my_commands(commands)

    description_text = (
        "💳 Привет! Я твой личный менеджер подписок и регулярных расходов.\n\n"
        "Я помогу:\n"
        "• Сохранить все ваши подписки (YouTube, Telegram Premium, VPN и др.)\n"
        "• Напомнить о предстоящих списаниях\n"
        "• Показать наглядную аналитику твоего бюджета за месяц\n\n"
        "Нажми «Запустить» или введи /start, чтобы начать!"
    )
    await bot.set_my_description(description_text)

    await bot.set_my_short_description("Удобный менеджер подписок и регулярных расходов 📊")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    await init_db()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(add_sub_router)
    dp.include_router(list_subs_router)
    dp.include_router(stats_router)

    await setup_bot_metadata(bot)

    notification_scheduler = NotificationScheduler(bot)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        notification_scheduler.check_upcoming_payments,
        trigger="cron",
        hour=9,
        minute=0
    )
    scheduler.start()

    logging.info("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())