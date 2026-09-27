from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.deps import get_db
from models.users_model import User


router = APIRouter(
    prefix="/public",
    tags=["public"]
)


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