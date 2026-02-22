from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
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
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
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
    ku_kod: Mapped[int | None] = mapped_column(Integer)
    ku_nazev: Mapped[str | None] = mapped_column(String(200))
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
    search_vector = Column(TSVECTOR)

    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
    favorites: Mapped[list["Favorite"]] = relationship(
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


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    property_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    property: Mapped["Property"] = relationship(back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("session_id", "property_id", name="uq_favorite"),
    )


class EmailSubscription(Base):
    __tablename__ = "email_subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    property_type: Mapped[str | None] = mapped_column(String(30))
    transaction_type: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(200))
    disposition: Mapped[str | None] = mapped_column(Text)
    price_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    price_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    size_min: Mapped[float | None] = mapped_column(Numeric(10, 2))
    size_max: Mapped[float | None] = mapped_column(Numeric(10, 2))
    notify_new: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_price_drop: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PragueKU(Base):
    __tablename__ = "prague_ku"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ku_kod: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    ku_nazev: Mapped[str] = mapped_column(String(200), nullable=False)
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)


class KuPriceStats(Base):
    __tablename__ = "ku_price_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ku_kod: Mapped[int] = mapped_column(Integer, nullable=False)
    ku_nazev: Mapped[str] = mapped_column(String(200), nullable=False)
    property_type: Mapped[str | None] = mapped_column(String(30))
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    median_price_m2: Mapped[float | None] = mapped_column(Numeric(14, 2))
    avg_price_m2: Mapped[float | None] = mapped_column(Numeric(14, 2))
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("ku_kod", "property_type", "transaction_type",
                         name="uq_ku_price_stats"),
    )


class ReferenceBenchmark(Base):
    __tablename__ = "reference_benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(200), nullable=False)
    property_type: Mapped[str | None] = mapped_column(String(30))
    transaction_type: Mapped[str | None] = mapped_column(String(20))
    price_m2: Mapped[float | None] = mapped_column(Numeric(14, 2))
    period: Mapped[str | None] = mapped_column(String(20))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("source", "region", "property_type", "transaction_type",
                         "period", name="uq_ref_benchmark"),
    )
