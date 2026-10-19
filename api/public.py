from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.deps import get_db
from models.users_model import User


router = APIRouter(
    prefix="/public",
    tags=["public"]
)


@router.get("/catalog")
async def get_catalog(
    tags: list[str] = Query(default=[], description="Теги аккаунта; можно передать несколько раз"),
    q: str | None = Query(default=None, min_length=1, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Публичный каталог аккаунтов с фильтром по тегам и постраничной выдачей.

    Для фильтрации все переданные теги должны присутствовать в `users.tags`.
    Например: `/public/catalog?tags=music&tags=moscow&page=1&page_size=20`.
    """
    conditions = [User.tags.has_key(tag) for tag in dict.fromkeys(tags)]
    if q:
        search = f"%{q.strip()}%"
        conditions.append(
            or_(
                User.username.ilike(search),
                User.display_name.ilike(search),
                User.profile_description.ilike(search),
            )
        )

    total_result = await db.execute(
        select(func.count(User.id)).where(*conditions)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(User)
        .options(selectinload(User.photos))
        .where(*conditions)
        .order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = result.scalars().all()

    return {
        "items": [
            {
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "description": user.profile_description,
                "tags": user.tags or {},
                "owner_verified": user.owner_verified,
                "service_verified": user.service_verified,
                "photos": [photo.image_url for photo in user.photos],
            }
            for user in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/profile/{username}")
async def get_public_profile(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.photos),
            selectinload(User.items)
        )
        .where(User.username == username)
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "owner_verified": user.owner_verified,
        "service_verified": user.service_verified,

        "photos": [
            photo.image_url
            for photo in user.photos
        ],

        "description": user.profile_description,

        "items": [
            {
                "name": item.name,
                "link_id": item.link_id
            }
            for item in user.items
        ],

        "extra": user.profile_extra_info,

        "blocks": [
            "gallery",
            "description",
            "links",
            "extra"
        ]
    }


@router.get("/last-users")
async def get_last_users(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User)
        .order_by(User.id.desc())
        .limit(10)
    )

    users = result.scalars().all()

    return [
        {
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url
        }
        for user in users
    ]
