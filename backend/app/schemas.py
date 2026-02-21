from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PropertyBase(BaseModel):
    source: str
    external_id: str
    url: str | None = None
    title: str | None = None
    description: str | None = None
    property_type: str | None = None
    transaction_type: str | None = None
    disposition: str | None = None
    price: float | None = None
    price_currency: str = "CZK"
    size_m2: float | None = None
    rooms: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    city: str | None = None
    district: str | None = None
    address: str | None = None
    images: list[str] = []


class PropertyResponse(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    duplicate_of: int | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime


class PropertyDetailResponse(PropertyResponse):
    price_history: list["PriceHistoryResponse"] = []
    raw_data: dict = {}


class PriceHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    price: float
    price_per_m2: float | None = None
    recorded_at: datetime


class PropertyListResponse(BaseModel):
    items: list[PropertyResponse]
    total: int
    page: int
    per_page: int
    pages: int


class StatsResponse(BaseModel):
    total_active: int
    new_today: int
    price_drops_today: int
    removed_today: int
    by_source: dict[str, int]
    by_type: dict[str, int]
    by_transaction: dict[str, int]


class UserFilterCreate(BaseModel):
    telegram_chat_id: int
    name: str = "My Filter"
    property_type: str | None = None
    transaction_type: str | None = None
    city: str | None = None
    district: str | None = None
    disposition: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    size_min: float | None = None
    size_max: float | None = None
    notify_new: bool = True
    notify_price_drop: bool = True
    price_drop_threshold: float = 5.0


class UserFilterResponse(UserFilterCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active: bool
    created_at: datetime


class UserFilterUpdate(BaseModel):
    name: str | None = None
    property_type: str | None = None
    transaction_type: str | None = None
    city: str | None = None
    district: str | None = None
    disposition: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    size_min: float | None = None
    size_max: float | None = None
    notify_new: bool | None = None
    notify_price_drop: bool | None = None
    price_drop_threshold: float | None = None
    active: bool | None = None
