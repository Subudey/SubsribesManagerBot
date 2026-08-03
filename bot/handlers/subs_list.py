from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, delete

from bot.database.db import async_session
from bot.database.models import Subscription
from bot.handlers.start import get_back_to_menu_keyboard

router = Router()

async def build_subs_list_payload(user_id: int):
    async with async_session() as session:
        query = select(Subscription).where(Subscription.user_id == user_id)
        result = await session.execute(query)
        subscriptions = result.scalars().all()

    if not subscriptions:
        text = (
            "📭 <b>У тебя пока нет сохранённых подписок.</b>\n\n"
            "Нажми кнопку ниже, чтобы вернуться в меню."
        )
        return text, get_back_to_menu_keyboard()

    text = "📋 <b>Твои активные подписки:</b>\n"
    text += "───────────────────\n\n"

    inline_keyboard = []
    for sub in subscriptions:
        text += (
            f"🔹 <b>{sub.title}</b>\n"
            f"├ 💳 Стоимость: <code>{sub.amount} {sub.currency}</code>\n"
            f"└ 🗓 Списание: {sub.billing_day}-го числа\n\n"
        )
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🗑 Удалить {sub.title}",
                callback_data=f"delete_sub_{sub.id}"
            )
        ])

    text += "───────────────────\n"
    text += "<i>Нажми на кнопку с корзиной, чтобы удалить подписку.</i>"

    inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_main_menu")
    ])

    return text, InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


@router.callback_query(F.data == "list_subscriptions")
async def list_subs_handler(callback: CallbackQuery, state: FSMContext):
    text, keyboard = await build_subs_list_payload(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("delete_sub_"))
async def delete_sub_handler(callback: CallbackQuery):
    sub_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        stmt = delete(Subscription).where(
            Subscription.id == sub_id,
            Subscription.user_id == callback.from_user.id
        )
        await session.execute(stmt)
        await session.commit()

    await callback.answer("🗑 Подписка удалена!", show_alert=False)

    text, keyboard = await build_subs_list_payload(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")