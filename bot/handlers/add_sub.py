from aiogram import Router, F, html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.handlers.start import get_back_to_menu_keyboard
from bot.database.db import async_session
from bot.database.models import Subscription

router = Router()


class AddSubscriptionSG(StatesGroup):
    title = State()
    amount = State()
    currency = State()
    billing_day = State()


@router.callback_query(F.data == "add_subscription")
async def start_add_sub(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSubscriptionSG.title)
    await callback.message.edit_text(
        "📝 Введи название подписки или сервиса:\n"
        "(Например: Netflix, VPS Hetzner, Яндекс Плюс)"
    )
    await callback.answer()


@router.message(AddSubscriptionSG.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddSubscriptionSG.amount)
    await message.answer("💰 Введи стоимость (только число, например: `500` или `9.99`):")


@router.message(AddSubscriptionSG.amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Пожалуйста, введи корректное положительное число!")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddSubscriptionSG.currency)

    currency_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="RUB (₽)", callback_data="curr_RUB"),
                InlineKeyboardButton(text="USD ($)", callback_data="curr_USD"),
                InlineKeyboardButton(text="EUR (€)", callback_data="curr_EUR"),
            ]
        ]
    )
    await message.answer("💱 Выбери валюту:", reply_markup=currency_kb)


@router.callback_query(AddSubscriptionSG.currency, F.data.startswith("curr_"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)
    await state.set_state(AddSubscriptionSG.billing_day)

    await callback.message.edit_text(
        "📅 Введи день месяца для списания (число от 1 до 31):\n"
        "(Например, если списание 15-го числа — введи 15)"
    )
    await callback.answer()


@router.message(AddSubscriptionSG.billing_day)
async def process_billing_day(message: Message, state: FSMContext):
    try:
        day = int(message.text)
        if not (1 <= day <= 31):
            raise ValueError
    except ValueError:
        await message.answer("❌ День месяца должен быть числом от 1 до 31!")
        return

    user_data = await state.get_data()

    async with async_session() as session:
        new_sub = Subscription(
            user_id=message.from_user.id,
            title=user_data["title"],
            amount=user_data["amount"],
            currency=user_data["currency"],
            billing_day=day
        )
        session.add(new_sub)
        await session.commit()

    await state.clear()

    await message.answer(
        f"✅ **Подписка успешно добавлена!**\n\n"
        f"📌 **Название:** {user_data['title']}\n"
        f"💳 **Стоимость:** {user_data['amount']} {user_data['currency']}\n"
        f"🗓 **День списания:** {day}-е число каждого месяца",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="Markdown"
    )