from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Float,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    property_type: Mapped[str | None] = mapped_column(String(30))
    transaction_type: Mapped[str | None] = mapped_column(String(20))
    disposition: Mapped[str | None] = mapped_column(String(20))
    price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    price_currency: Mapped[str] = mapped_column(String(10), default="CZK")
    size_m2: Mapped[float | None] = mapped_column(Numeric(10, 2))
    rooms: Mapped[int | None] = mapped_column(Integer)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    city: Mapped[str | None] = mapped_column(String(200))
    district: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text)
    images: Mapped[dict] = mapped_column(JSONB, default=list)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="active")
    duplicate_of: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("properties.id", ondelete="SET NULL")
    )
    missed_runs: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external"),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    price_per_m2: Mapped[float | None] = mapped_column(Numeric(14, 2))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    property: Mapped["Property"] = relationship(back_populates="price_history")


class UserFilter(Base):
    __tablename__ = "user_filters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user_filter", cascade="all, delete-orphan"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_filter_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user_filters.id", ondelete="CASCADE")
    )
    property_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("properties.id", ondelete="CASCADE")
    )
    notification_type: Mapped[str] = mapped_column(String(30), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user_filter: Mapped["UserFilter"] = relationship(back_populates="notifications")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    listings_found: Mapped[int] = mapped_column(Integer, default=0)
    listings_new: Mapped[int] = mapped_column(Integer, default=0)
    listings_updated: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="running")
