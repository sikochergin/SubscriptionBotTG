from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_subscription_filters_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Активные", callback_data="subs_filter_active"),
                InlineKeyboardButton(text="Отложенные", callback_data="subs_filter_delayed"),
            ],
            [
                InlineKeyboardButton(text="Просроченные", callback_data="subs_filter_expired"),
                InlineKeyboardButton(text="Удалённые", callback_data="subs_filter_deleted"),
            ],
            [InlineKeyboardButton(text="Все", callback_data="subs_filter_all")],
            [InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]
        ]
    )

def get_subscription_card_notdeleted_keyboard(subscription_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Продлить", callback_data=f"subs_card_notdeleted_extend_{subscription_id}")],
            [InlineKeyboardButton(text="Отложить", callback_data=f"subs_card_notdeleted_delay_{subscription_id}")],
            [InlineKeyboardButton(text="Редактировать", callback_data=f"subs_card_notdeleted_edit_{subscription_id}")],
            [InlineKeyboardButton(text="История оплат", callback_data=f"subs_card_payment_history_{subscription_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"subs_card_notdeleted_delete_{subscription_id}")],
            [InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]
        ]
    )

def get_subscription_card_deleted_keyboard(subscription_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="История оплат", callback_data=f"subs_card_payment_history_{subscription_id}")],
            [InlineKeyboardButton(text="Восстановить", callback_data=f"subs_card_deleted_recover_{subscription_id}")],
            [InlineKeyboardButton(text="В главное меню", callback_data="go_main_menu")]
        ]
    )