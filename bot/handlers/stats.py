from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.database.db import async_session
from bot.database.models import Subscription
from bot.handlers.start import get_back_to_menu_keyboard

router = Router()

@router.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    async with async_session() as session:
        query = select(Subscription).where(Subscription.user_id == callback.from_user.id)
        result = await session.execute(query)
        subscriptions = result.scalars().all()

    if not subscriptions:
        await callback.message.edit_text(
            "📭 У тебя пока нет подписок для расчета аналитики.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await callback.answer()
        return

    totals = {}
    for sub in subscriptions:
        totals[sub.currency] = totals.get(sub.currency, 0.0) + sub.amount

    stats_text = "📊 **Твой ежемесячный бюджет на подписки:**\n\n"
    for currency, total in totals.items():
        stats_text += f"▪️ **{total:.2f} {currency}** в месяц\n"

    stats_text += f"\nВсего активных сервисов: **{len(subscriptions)}**"

    await callback.message.edit_text(stats_text, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown")
    await callback.answer()