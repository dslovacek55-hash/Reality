from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import UserFilter
from app.schemas import UserFilterCreate, UserFilterResponse, UserFilterUpdate

router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.post("", response_model=UserFilterResponse)
async def create_filter(
    data: UserFilterCreate, db: AsyncSession = Depends(get_db)
):
    uf = UserFilter(**data.model_dump())
    db.add(uf)
    await db.commit()
    await db.refresh(uf)
    return UserFilterResponse.model_validate(uf)


@router.get("/chat/{chat_id}", response_model=list[UserFilterResponse])
async def get_filters_by_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    query = select(UserFilter).where(UserFilter.telegram_chat_id == chat_id)
    result = await db.execute(query)
    return [UserFilterResponse.model_validate(f) for f in result.scalars().all()]


@router.get("/{filter_id}", response_model=UserFilterResponse)
async def get_filter(filter_id: int, db: AsyncSession = Depends(get_db)):
    query = select(UserFilter).where(UserFilter.id == filter_id)
    result = await db.execute(query)
    uf = result.scalar_one_or_none()
    if not uf:
        raise HTTPException(status_code=404, detail="Filter not found")
    return UserFilterResponse.model_validate(uf)


@router.patch("/{filter_id}", response_model=UserFilterResponse)
async def update_filter(
    filter_id: int, data: UserFilterUpdate, db: AsyncSession = Depends(get_db)
):
    query = select(UserFilter).where(UserFilter.id == filter_id)
    result = await db.execute(query)
    uf = result.scalar_one_or_none()
    if not uf:
        raise HTTPException(status_code=404, detail="Filter not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(uf, key, value)

    await db.commit()
    await db.refresh(uf)
    return UserFilterResponse.model_validate(uf)


@router.delete("/{filter_id}")
async def delete_filter(filter_id: int, db: AsyncSession = Depends(get_db)):
    query = select(UserFilter).where(UserFilter.id == filter_id)
    result = await db.execute(query)
    uf = result.scalar_one_or_none()
    if not uf:
        raise HTTPException(status_code=404, detail="Filter not found")

    await db.delete(uf)
    await db.commit()
    return {"ok": True}
