from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.security import hash_password, get_current_user
from core.config import settings
from models.user import User
from db.deps import get_db  # твоя async сессия
from fastapi import status

from pydantic import BaseModel

from db.crud_user import delete_user_by_id

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/register", status_code=201)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем, есть ли уже такой пользователь
    result = await db.execute(
        select(User).where((User.username == user.username) | (User.email == user.email))
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}


@router.delete("/delete/me", status_code=204)
async def delete_me(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await delete_user_by_id(db, current_user.id)
    return


@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()



