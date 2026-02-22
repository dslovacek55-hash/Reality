"""
Lightweight ORM models for the Telegram bot.
These mirror the backend's database schema (read/write to the same tables).
Keep in sync with backend/app/models.py when schema changes.
"""
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric,
    String, Text, Float,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str] = mapped_column(String(100))
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    property_type: Mapped[str | None] = mapped_column(String(30))
    transaction_type: Mapped[str | None] = mapped_column(String(20))
    disposition: Mapped[str | None] = mapped_column(String(20))
    price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    size_m2: Mapped[float | None] = mapped_column(Numeric(10, 2))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    city: Mapped[str | None] = mapped_column(String(200))
    district: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))
    first_seen_at: Mapped[None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[None] = mapped_column(DateTime(timezone=True))


class UserFilter(Base):
    __tablename__ = "user_filters"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(200), default="My Filter")
    property_type: Mapped[str | None] = mapped_column(String(30))
    transaction_type: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(200))
    district: Mapped[str | None] = mapped_column(String(200))
    disposition: Mapped[str | None] = mapped_column(Text)
    price_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    price_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    size_min: Mapped[float | None] = mapped_column(Numeric(10, 2))
    size_max: Mapped[float | None] = mapped_column(Numeric(10, 2))
    notify_new: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_price_drop: Mapped[bool] = mapped_column(Boolean, default=True)
    price_drop_threshold: Mapped[float] = mapped_column(Numeric(5, 2), default=5.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_filter_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("user_filters.id"))
    property_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("properties.id"))
    notification_type: Mapped[str] = mapped_column(String(30))
    sent_at: Mapped[None] = mapped_column(DateTime(timezone=True), server_default=func.now())
