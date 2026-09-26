from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, get_current_user
from models.users_model import User
from db.deps import get_db
from db.crud_user import delete_user_by_id


router = APIRouter(
    prefix="/users",
    tags=["users"]
)


# ============================================================
# Schemas
# ============================================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    profile_description: str | None = None
    profile_extra_info: str | None = None
    avatar_url: str | None = None


# ============================================================
# GET /users/me
# ============================================================

@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "profile_description": current_user.profile_description,
        "profile_extra_info": current_user.profile_extra_info,
        "avatar_url": current_user.avatar_url,
        "owner_verified": current_user.owner_verified,
        "service_verified": current_user.service_verified,
    }


# ============================================================
# PATCH /users/me
# ============================================================

@router.patch("/me")
async def update_me(
    profile: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = profile.model_dump(
        exclude_unset=True
    )

    for field, value in data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "profile_description": current_user.profile_description,
        "profile_extra_info": current_user.profile_extra_info,
        "avatar_url": current_user.avatar_url,
        "owner_verified": current_user.owner_verified,
        "service_verified": current_user.service_verified,
    }


# ============================================================
# POST /users/register
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(
            (User.username == user.username) |
            (User.email == user.email)
        )
    )

    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(db_user)

    await db.commit()
    await db.refresh(db_user)

    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email
    }


# ============================================================
# DELETE /users/delete/me
# ============================================================

@router.delete(
    "/delete/me",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await delete_user_by_id(
        db,
        current_user.id
    )

    return


# ============================================================
# DELETE /users/delete/{user_id}
# ============================================================

@router.delete(
    "/delete/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()

    return