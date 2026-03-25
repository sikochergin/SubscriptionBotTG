from datetime import datetime, date

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class Subscription(Base):
    __tablename__ = "tbl_subscription"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creationdatetime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    modificationdatetime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    enddatetime: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

class PaymentHistory(Base):
    __tablename__ = "tbl_payment_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("tbl_subscription.id"), nullable=False)
    creationdatetime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    new_enddatetime: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)