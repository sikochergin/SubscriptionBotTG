from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

from app.states import SubscriptionStates
from app.database import async_session_maker
from app.config import settings
from app.keyboards.subscriptions import get_subscription_filters_keyboard, get_subscription_card_notdeleted_keyboard, get_subscription_card_deleted_keyboard
from app.models import Subscription, PaymentHistory

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_id_list


@router.message(F.text == "📋 Список подписок")
async def show_subscriptions_menu(message: Message) -> None:
    if message.chat.type != "private":
        return

    if not message.from_user or not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return

    await message.answer(
        "Выберите категорию подписок:",
        reply_markup=get_subscription_filters_keyboard(),
    )


@router.callback_query(F.data.startswith("subs_filter_"))
async def process_subscription_filter(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return

    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    filter_value = callback.data.replace("subs_filter_", "")

    async with async_session_maker() as session:
        if (filter_value == "all"):
            result = await session.execute(select(Subscription).where(Subscription.deleted == False).order_by(Subscription.name))
        elif (filter_value == "deleted"):
            result = await session.execute(select(Subscription).where(Subscription.deleted == True).order_by(Subscription.name))
        else:
            result = await session.execute(select(Subscription).where(Subscription.status == filter_value).where(Subscription.deleted == False).order_by(Subscription.name))
        
        subscriptions = result.scalars().all()

    inline_markup = []

    for sub in subscriptions:
        inline_markup.append([InlineKeyboardButton(text=f"Подписка {sub.name}", callback_data=f"sub_select_by_id_{sub.id}")])
    inline_markup.append([InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")])

    murkup = InlineKeyboardMarkup(inline_keyboard=inline_markup)

    await callback.message.answer(
        text="Подписки по вашему запросу:",
        reply_markup=murkup,
    )

    await callback.answer()


@router.callback_query(F.data.startswith("sub_select_by_id_"))
async def process_subscription_card(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return

    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    subscription_id = int(callback.data.replace("sub_select_by_id_", ""))

    async with async_session_maker() as session:
        subscription = (await session.execute(select(Subscription).where(Subscription.id == subscription_id))).scalar_one_or_none()

    if (not subscription.deleted):
        inline_markup = get_subscription_card_notdeleted_keyboard(subscription_id)
        subscription_status = subscription.status
    else:
        inline_markup = get_subscription_card_deleted_keyboard(subscription_id)
        subscription_status = "deleted"

    reply_message = f"Подписка {subscription.name}\n\nДата окончания: {subscription.enddatetime}\nЦена: {subscription.amount}\nСтатус: {subscription_status}"

    await callback.message.answer(
        text=reply_message,
        reply_markup=inline_markup,
    )

    await callback.answer()


#----------------
#Продление подписки
#----------------
@router.callback_query(F.data.startswith("subs_card_notdeleted_extend_"))
async def process_subscription_extend(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return

    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    subscription_id = int(callback.data.replace("subs_card_notdeleted_extend_", ""))
    await state.set_state(SubscriptionStates.waiting_for_price_to_extend)

    await state.update_data(subscription_id=subscription_id)
    await callback.message.answer("На какую сумму была произведена оплата?")
    await callback.answer()

@router.message(SubscriptionStates.waiting_for_price_to_extend)
async def process_date_to_extend(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("Неверный формат. Пожалуйста, введите целое число.")
        return

    await state.update_data(amount=amount)
    await state.set_state(SubscriptionStates.waiting_for_date_to_extend)

    await message.answer("На какую дату вы хотите продлить подписку? (формат: YYYY-MM-DD)")

@router.message(SubscriptionStates.waiting_for_date_to_extend)
async def process_date_to_extend(message: Message, state: FSMContext):
    try:
        new_date = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, используйте формат YYYY-MM-DD.")
        return

    data = await state.get_data()
    subscription_id = data.get('subscription_id')

    async with async_session_maker() as session:
        subscription = (await session.execute(select(Subscription).where(Subscription.id == subscription_id))).scalar_one_or_none()

        if subscription:
            extra_message_price = ""
            if (subscription.amount != int(data["amount"])):
                subscription.amount = int(data["amount"])
                extra_message_price = f' Цена подписки изменена на {data["amount"]}.'
            subscription.enddatetime = new_date
            subscription.status = "active"

            new_payment_history = PaymentHistory(
                subscription_id=subscription.id,
                new_enddatetime = new_date,
                amount=subscription.amount,
            )
            session.add(new_payment_history)
            
            await session.commit()

            await session.commit()

            await message.answer(f"Подписка успешно продлена до {new_date}.{extra_message_price}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        else:
            await message.answer("Подписка не найдена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))

    await state.clear()


#----------------
#Откладывание подписки
#----------------
@router.callback_query(F.data.startswith("subs_card_notdeleted_delay_"))
async def process_subscription_delay(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return

    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    subscription_id = int(callback.data.replace("subs_card_notdeleted_delay_", ""))
    await state.set_state(SubscriptionStates.waiting_for_date_to_delay)

    await state.update_data(subscription_id=subscription_id)
    await callback.message.answer("На какую дату вы хотите отложить подписку? (формат: YYYY-MM-DD)")
    await callback.answer()

@router.message(SubscriptionStates.waiting_for_date_to_delay)
async def process_date_to_delay(message: Message, state: FSMContext):
    try:
        new_date = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, используйте формат YYYY-MM-DD.")
        return

    data = await state.get_data()
    subscription_id = data.get('subscription_id')

    async with async_session_maker() as session:
        subscription = (await session.execute(select(Subscription).where(Subscription.id == subscription_id))).scalar_one_or_none()

        if subscription:
            subscription.enddatetime = new_date
            subscription.status = "delayed"
            await session.commit()

            await message.answer(f"Подписка успешно отложена до {new_date}.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        else:
            await message.answer("Подписка не найдена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))

    await state.clear()
    

#----------------
#Удаление подписки
#----------------
@router.callback_query(F.data.startswith("subs_card_notdeleted_delete_"))
async def process_subscription_delete(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return

    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    subscription_id = int(callback.data.replace("subs_card_notdeleted_delete_", ""))
    await state.set_state(SubscriptionStates.waiting_for_accept_to_delete)

    await state.update_data(subscription_id=subscription_id)
    await callback.message.answer('Вы уверены, что хотите удалить подписку? Если да, напишите "Удалить".')
    await callback.answer()

@router.message(SubscriptionStates.waiting_for_accept_to_delete)
async def process_accept_to_delete(message: Message, state: FSMContext):
    if (message.text != "Удалить"):
        await message.answer("Отмена удаления подписки", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        await state.clear()

    data = await state.get_data()
    subscription_id = data.get('subscription_id')

    async with async_session_maker() as session:
        subscription = (await session.execute(select(Subscription).where(Subscription.id == subscription_id))).scalar_one_or_none()

        if subscription:
            subscription.deleted = True
            await session.commit()

            await message.answer(f"Подписка успешно удалена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        else:
            await message.answer("Подписка не найдена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))

    await state.clear()
    

#----------------
#Редактирование подписки
#----------------
@router.callback_query(F.data.startswith("subs_card_notdeleted_edit_"))
async def process_subscription_edit(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return

    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    subscription_id = int(callback.data.replace("subs_card_notdeleted_edit_", ""))
    await state.set_state(SubscriptionStates.waiting_for_accept_to_edit)

    await state.update_data(subscription_id=subscription_id)
    await callback.message.answer('Что вы хотите изменить (Название/Цена/Статус/Дата Окончания)? (формат: Поле - Значение)')
    await callback.answer()

@router.message(SubscriptionStates.waiting_for_accept_to_edit)
async def process_accept_to_edit(message: Message, state: FSMContext):
    mes = message.text.split(' - ')
    if (len(mes) != 2):
        await message.answer("Неверный формат. Пожалуйста, используйте формат Поле - Значение")
        return
    
    if (mes[0] not in ["Название", "Цена", "Статус", "Дата Окончания"]):
        await message.answer("Неверный формат. Пожалуйста, используйте поле из предложенного списка (Название/Цена/Статус/Дата Окончания).")
        return
    
    data = await state.get_data()
    subscription_id = data.get('subscription_id')

    async with async_session_maker() as session:
        subscription = (await session.execute(select(Subscription).where(Subscription.id == subscription_id))).scalar_one_or_none()

        if (mes[0] == "Название"):
            if subscription:
                subscription.name = mes[1]
                await session.commit()

                await message.answer(f"Название подписки изменено на {mes[1]}.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
            else:
                await message.answer("Подписка не найдена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        elif (mes[0] == "Цена"):
            try:
                new_amount = int(mes[1])
            except:
                await message.answer("Неверный формат цены. Пожалуйста, челое значение.")
                return

            if subscription:
                subscription.amount = new_amount
                await session.commit()

                await message.answer(f"Цена подписки изменена на {mes[1]}.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
            else:
                await message.answer("Подписка не найдена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        elif (mes[0] == "Статус"):
            if (mes[1] not in ["active", "delayed", "expired"]):
                await message.answer("Неверное значение статуса. Пожалуйста, используйте статус из списка: active, delayed, expired.")
                return

            if subscription:
                subscription.status = mes[1]
                await session.commit()

                await message.answer(f"Статус подписки изменен на {mes[1]}.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
            else:
                await message.answer("Подписка не найдена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        else:
            try:
                new_date = datetime.strptime(message.text, "%Y-%m-%d").date()
            except ValueError:
                await message.answer("Неверный формат даты. Пожалуйста, используйте формат YYYY-MM-DD.")
                return
            
            if subscription:
                subscription.enddatetime = new_date
                await session.commit()

                await message.answer(f"Дата окончания подписки успешно изменена на {new_date}.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
            else:
                await message.answer("Подписка не найдена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))

    await state.clear()


#----------------
#Восстановление подписки
#----------------
@router.callback_query(F.data.startswith("subs_card_deleted_recover_"))
async def process_subscription_recover(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return

    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    subscription_id = int(callback.data.replace("subs_card_deleted_recover_", ""))
    await state.set_state(SubscriptionStates.waiting_for_accept_to_recover)

    await state.update_data(subscription_id=subscription_id)
    await callback.message.answer('Вы уверены, что хотите восстановить подписку? Если да, напишите "Восстановить".')
    await callback.answer()

@router.message(SubscriptionStates.waiting_for_accept_to_recover)
async def process_accept_to_recover(message: Message, state: FSMContext):
    if (message.text != "Восстановить"):
        await message.answer("Отмена восстановления подписки", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        await state.clear()

    data = await state.get_data()
    subscription_id = data.get('subscription_id')

    async with async_session_maker() as session:
        subscription = (await session.execute(select(Subscription).where(Subscription.id == subscription_id))).scalar_one_or_none()

        if subscription:
            subscription.deleted = False
            await session.commit()

            await message.answer(f"Подписка успешно восстановлена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
        else:
            await message.answer("Подписка не найдена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))

    await state.clear()



@router.callback_query(F.data.startswith("subs_card_payment_history_"))
async def process_subscription_payment_history(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return

    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    subscription_id = int(callback.data.replace("subs_card_payment_history_", ""))
    
    async with async_session_maker() as session:
        payment_history = (await session.execute(select(PaymentHistory).where(PaymentHistory.subscription_id == subscription_id))).scalars().all()
        subscription = (await session.execute(select(Subscription).where(Subscription.id == subscription_id))).scalar_one_or_none()


        mess = f"История оплат для подписки {subscription.name}"
        for ph in payment_history:
            mess += f"\n\nВремя продления: {ph.creationdatetime}\nПродлена до: {ph.new_enddatetime}\nПродлена на сумму: {ph.amount}"
        await callback.message.answer(mess, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]]))
    await callback.answer()