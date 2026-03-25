from aiogram.fsm.state import StatesGroup, State


class SubscriptionStates(StatesGroup):
    waiting_for_date_to_delay = State()  # Состояние, когда бот ожидает дату для отложенной подписки
    waiting_for_accept_to_delete = State()  # Для подтверждения удаления
    waiting_for_accept_to_edit = State()  # Для редактирования значений
    waiting_for_price_to_extend = State()  # Для продления цена
    waiting_for_date_to_extend = State()  # Для продления дата
    waiting_for_accept_to_recover = State() # Для восстановления

    wating_for_information_to_add_sub_name = State() # Для добавления подписки - Имя
    wating_for_information_to_add_sub_date = State() # Для добавления подписки - Дата
    wating_for_information_to_add_sub_price = State() # Для добавления подписки - Цена
    wating_for_information_to_add_sub_status = State() # Для добавления подписки - Статус