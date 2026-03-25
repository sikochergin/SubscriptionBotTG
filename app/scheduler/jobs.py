from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlalchemy import select
import pytz

from app.database import async_session_maker
from app.models import Subscription
from app.handlers.notification import send_active_subs_notification, send_delayed_subs_notification

def start_scheduler():
    scheduler = AsyncIOScheduler()
    moscow_tz = pytz.timezone("Europe/Moscow")

    trigger = CronTrigger(hour=3, minute=34, second=0, timezone=moscow_tz)
    scheduler.add_job(daily_task, trigger)

    scheduler.start()

    print("Scheduler started. Задачи будут выполняться каждый день в 10:00 по МСК.")


async def daily_task():
    async with async_session_maker() as session:
        active_subs = []
        active_subs += (await session.execute(select(Subscription).where(Subscription.deleted == False)
                                                .where(Subscription.enddatetime == datetime.utcnow().date() + timedelta(days=3))
                                                .where(Subscription.status == 'active').order_by(Subscription.name))).scalars().all()
        active_subs += (await session.execute(select(Subscription).where(Subscription.deleted == False)
                                                .where(Subscription.enddatetime == datetime.utcnow().date() + timedelta(days=5))
                                                .where(Subscription.status == 'active').order_by(Subscription.name))).scalars().all()
        active_subs += (await session.execute(select(Subscription).where(Subscription.deleted == False)
                                                .where(Subscription.enddatetime == datetime.utcnow().date() + timedelta(days=10))
                                                .where(Subscription.status == 'active').order_by(Subscription.name))).scalars().all()
        
        delayed_subs = []
        delayed_subs += (await session.execute(select(Subscription).where(Subscription.deleted == False)
                                                .where(Subscription.enddatetime == (datetime.utcnow().date() + timedelta(days=3)))
                                                .where(Subscription.status == 'delayed').order_by(Subscription.name))).scalars().all()
        delayed_subs += (await session.execute(select(Subscription).where(Subscription.deleted == False)
                                                .where(Subscription.enddatetime == datetime.utcnow().date() + timedelta(days=5))
                                                .where(Subscription.status == 'delayed').order_by(Subscription.name))).scalars().all()
        
        await session.commit()

        await send_active_subs_notification(active_subs)
        await send_delayed_subs_notification(delayed_subs)