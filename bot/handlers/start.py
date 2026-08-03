from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_subscription"),
            ],
            [
                InlineKeyboardButton(text="📋 Мои подписки", callback_data="list_subscriptions"),
                InlineKeyboardButton(text="📊 Аналитика", callback_data="stats"),
            ]
        ]
    )


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Универсальная кнопка Возврата в меню"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_main_menu")]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        f"Привет, {html.bold(message.from_user.full_name)}! 👋\n\n"
        f"Я твой личный менеджер подписок и регулярных расходов.\n"
        f"Управляй своими сервисами прямо из этого меню!"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_menu_handler(callback: CallbackQuery):
    welcome_text = (
        f"Привет, {html.bold(callback.from_user.full_name)}! 👋\n\n"
        f"Я твой личный менеджер подписок и регулярных расходов.\n"
        f"Управляй своими сервисами прямо из этого меню!"
    )
    await callback.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard())
    await callback.answer()