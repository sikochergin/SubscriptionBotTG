from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Список подписок")],
            [KeyboardButton(text="➕ Добавить подписку")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )