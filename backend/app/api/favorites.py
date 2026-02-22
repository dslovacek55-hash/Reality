from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Favorite, Property
from app.schemas import FavoriteCreate, FavoriteResponse, FavoriteWithProperty, PropertyResponse

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.post("", response_model=FavoriteResponse, status_code=201)
async def add_favorite(data: FavoriteCreate, db: AsyncSession = Depends(get_db)):
    # Check property exists
    prop = await db.get(Property, data.property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check if already favorited
    existing = await db.execute(
        select(Favorite).where(
            Favorite.session_id == data.session_id,
            Favorite.property_id == data.property_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already in favorites")

    fav = Favorite(session_id=data.session_id, property_id=data.property_id)
    db.add(fav)
    await db.commit()
    await db.refresh(fav)
    return FavoriteResponse.model_validate(fav)


@router.get("/{session_id}", response_model=list[FavoriteWithProperty])
async def get_favorites(session_id: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(Favorite)
        .options(selectinload(Favorite.property))
        .where(Favorite.session_id == session_id)
        .order_by(Favorite.created_at.desc())
    )
    result = await db.execute(query)
    favorites = result.scalars().all()
    return [
        FavoriteWithProperty(
            id=f.id,
            session_id=f.session_id,
            property_id=f.property_id,
            created_at=f.created_at,
            property=PropertyResponse.model_validate(f.property),
        )
        for f in favorites
    ]


@router.delete("/{session_id}/{property_id}", status_code=204)
async def remove_favorite(session_id: str, property_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        delete(Favorite).where(
            Favorite.session_id == session_id,
            Favorite.property_id == property_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    await db.commit()


@router.get("/{session_id}/ids", response_model=list[int])
async def get_favorite_ids(session_id: str, db: AsyncSession = Depends(get_db)):
    """Return just the property IDs for quick lookups."""
    result = await db.execute(
        select(Favorite.property_id).where(Favorite.session_id == session_id)
    )
    return [row[0] for row in result.all()]
