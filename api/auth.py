from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.deps import get_db
from schemas.user import UserCreate, UserLogin
from db.crud_user import (
    get_user_by_email,
    get_user_by_username,
    create_user
)

from core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):

    if await get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed = hash_password(user.password)

    new_user = await create_user(db, user, hashed)

    return new_user


@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):

    db_user = await get_user_by_email(db, user.email)

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }
