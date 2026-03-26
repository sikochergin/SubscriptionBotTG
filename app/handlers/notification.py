from aiogram import Router
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.models import Subscription

router = Router()

bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

group_chat_id = settings.group_chat_id

async def send_active_subs_notification(sub_list: list[Subscription]) -> None:
    print(f"Отправлено уведомление в чат {group_chat_id} 1")
    try:
        for sub in sub_list:
            await bot.send_message(group_chat_id, f"Внимание!\nЗаканчивается подписка {sub.name}.\nСрок действия: {sub.enddatetime}.\nСумма к оплате: {sub.amount} руб.")
    except Exception as e:
        print(f"Ошибка при отправке сообщения для подписки {sub.name}: {e}")

async def send_delayed_subs_notification(sub_list: list[Subscription]) -> None:
    print(f"Отправлено уведомление в чат {group_chat_id} 2")
    try:
        for sub in sub_list:
            await bot.send_message(group_chat_id, f"Внимание!\nЗаканчивается заморозка подписки {sub.name}.\nСрок действия заморозки: {sub.enddatetime}.\nСумма к оплате: {sub.amount} руб.")
    except Exception as e:
        print(f"Ошибка при отправке сообщения для подписки {sub.name}: {e}")