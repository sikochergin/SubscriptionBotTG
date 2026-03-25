from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

from app.states import SubscriptionStates
from app.database import async_session_maker
from app.config import settings
from app.models import Subscription

router = Router()

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="confirm_add_subscription_yes"),
                InlineKeyboardButton(text="Нет", callback_data="confirm_add_subscription_no"),
            ]
        ]
    )
def get_sub_statuses_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Активная", callback_data="add_subscription_status_active")],
            [InlineKeyboardButton(text="Отложенная", callback_data="add_subscription_status_delayed")],
            [InlineKeyboardButton(text="Просроченная", callback_data="add_subscription_status_expired")]
        ]
    )

def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_id_list

@router.message(F.text == "➕ Добавить подписку")
async def show_add_subscription(message: Message, state: FSMContext) -> None:
    if message.chat.type != "private":
        return

    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return

    await state.set_state(SubscriptionStates.wating_for_information_to_add_sub_name)

    await message.answer("Введите название подписки:")

@router.message(SubscriptionStates.wating_for_information_to_add_sub_name)
async def process_subscription_name(message: Message, state: FSMContext):
    name = message.text
    if not name:
        await message.answer("Название подписки не может быть пустым.")
        return

    await state.update_data(name=name)

    await state.set_state(SubscriptionStates.wating_for_information_to_add_sub_date)
    await message.answer("Укажите дату окончания подписки (формат: YYYY-MM-DD).")

@router.message(SubscriptionStates.wating_for_information_to_add_sub_date)
async def process_subscription_name(message: Message, state: FSMContext):
    try:
        new_date = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат! Введите дату в формате: YYYY-MM-DD.")
        return

    await state.update_data(date=new_date)

    await state.set_state(SubscriptionStates.wating_for_information_to_add_sub_price)
    await message.answer("Введите цену подписки.")

@router.message(SubscriptionStates.wating_for_information_to_add_sub_price)
async def process_subscription_name(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("Неверный формат! Введите целое число.")
        return

    await state.update_data(amount=amount)

    await state.set_state(SubscriptionStates.wating_for_information_to_add_sub_status)
    await message.answer("Выберите статус подписки.", reply_markup=get_sub_statuses_keyboard())

@router.callback_query(F.data.startswith("add_subscription_status_"))
async def process_subscription_name(callback: CallbackQuery, state: FSMContext):

    status = callback.data.replace("add_subscription_status_", "")
    
    await state.update_data(status=status)
    data = await state.get_data()

    name = data["name"]
    date = data["date"]
    amount = data["amount"]

    confirmation_message = (
        f"Подписка: {name}\n"
        f"Дата окончания: {date}\n"
        f"Цена: {amount}\n"
        f"Статус: {status}\n\n"
        "Добавить подписку?"
    )

    await callback.message.answer(confirmation_message, reply_markup=get_confirmation_keyboard())
    await callback.answer()
    await state.set_state(SubscriptionStates.waiting_for_confirmation_to_add)


@router.callback_query(F.data.startswith("confirm_add_subscription_"))
async def process_subscription_addition_accept(callback: CallbackQuery, state: FSMContext):
    if callback.message.chat.type != "private":
        await callback.answer()
        await state.clear()
        return
    
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        await state.clear()
        return
    
    if (callback.data.split("_")[-1] == "yes"):
        data = await state.get_data()
        name = data["name"]
        end_date = data["date"]
        amount = data["amount"]
        status = data["status"]

        async with async_session_maker() as session:
            new_subscription = Subscription(
                name=name,
                enddatetime=end_date,
                amount=amount,
                status=status,
                deleted=False,
            )
            session.add(new_subscription)
            await session.commit()

        await callback.message.answer(f"Подписка '{name}' успешно добавлена!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
    else:
        await callback.message.answer(f"Отмена добавления подписки '{name}'.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
    
    await state.clear()