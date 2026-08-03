import logging
from datetime import date
from aiogram import Bot
from sqlalchemy import select

from bot.database.db import async_session
from bot.database.models import Subscription

logger = logging.getLogger(__name__)


class NotificationScheduler:

    def __init__(self, bot: Bot):
        self.bot = bot

    async def check_upcoming_payments(self) -> None:
        today = date.today()
        logger.info(f"Запуск проверки списаний на дату: {today.strftime('%d.%m.%Y')}")

        async with async_session() as session:
            result = await session.execute(select(Subscription))
            subscriptions = result.scalars().all()

            for sub in subscriptions:
                billing_date = self._calculate_next_billing_date(today, sub.billing_day)
                if not billing_date:
                    continue

                days_left = (billing_date - today).days

                try:
                    if days_left == 0:
                        text = (
                            f"🚨 <b>Списание сегодня!</b>\n\n"
                            f"Сегодня ({billing_date.strftime('%d.%m')}) запланировано "
                            f"списание за <b>{sub.title}</b>.\n"
                            f"💳 Сумма: <code>{sub.amount} {sub.currency}</code>\n\n"
                            f"<i>Убедись, что на карте достаточно средств.</i>"
                        )
                        await self.bot.send_message(chat_id=sub.user_id, text=text, parse_mode="HTML")

                    elif days_left == 1:
                        text = (
                            f"⚠️ <b>Завтра списание!</b>\n\n"
                            f"Завтра ({billing_date.strftime('%d.%m')}) состоится "
                            f"списание за <b>{sub.title}</b>.\n"
                            f"💰 Сумма: <code>{sub.amount} {sub.currency}</code>"
                        )
                        await self.bot.send_message(chat_id=sub.user_id, text=text, parse_mode="HTML")

                    elif days_left == 3:
                        text = (
                            f"⏳ <b>Напоминание о подписке</b>\n\n"
                            f"Через <b>3 дня</b> ({billing_date.strftime('%d.%m')}) "
                            f"будет списание за <b>{sub.title}</b>.\n"
                            f"💰 Сумма: <code>{sub.amount} {sub.currency}</code>"
                        )
                        await self.bot.send_message(chat_id=sub.user_id, text=text, parse_mode="HTML")

                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления для user_id={sub.user_id}: {e}")

    @staticmethod
    def _calculate_next_billing_date(today: date, billing_day: int) -> date | None:
        try:
            target_date = date(today.year, today.month, billing_day)
        except ValueError:
            if today.month == 12:
                target_date = date(today.year, 12, 31)
            else:
                target_date = date(today.year, today.month + 1, 1)

        if target_date < today:
            if today.month == 12:
                next_year = today.year + 1
                next_month = 1
            else:
                next_year = today.year
                next_month = today.month + 1

            try:
                target_date = date(next_year, next_month, billing_day)
            except ValueError:
                target_date = date(next_year, next_month, 28)

        return target_date