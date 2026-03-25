from aiogram import Dispatcher

from app.handlers.start import router as start_router
from app.handlers.subscription_list import router as subscriptions_list_router
from app.handlers.subscription_add import router as subscriptions_add_router
from app.handlers.notification import router as notification_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(subscriptions_list_router)
    dp.include_router(subscriptions_add_router)
    dp.include_router(notification_router)