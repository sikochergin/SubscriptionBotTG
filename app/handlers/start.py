from aiogram import Router, F
from aiogram.filters import Command, or_f
from aiogram.types import Message, CallbackQuery

from app.config import settings
from app.keyboards.main_menu import get_main_menu

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_id_list


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if message.chat.type != "private":
        return

    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.", show_alert=True)
        return

    await message.answer(
        "Добрый день! Выберите действие с подписками.",
        reply_markup=get_main_menu(),
    )
    return
    
@router.callback_query(F.data == "go_main_menu")
async def go_main_menu(callback: CallbackQuery) -> None:
    if callback.message.chat.type != "private":
        await callback.answer()
        return

    await callback.message.answer(
        "Добрый день! Выберите действие с подписками.",
        reply_markup=get_main_menu(),
    )
    return


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if message.chat.type != "private":
        return

    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return

    await message.answer(
        "Пока доступны базовые команды:\n"
        "/start — запустить бота\n"
        "/help — помощь"
    )