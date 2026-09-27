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

from datetime import datetime, timedelta

from models.email_verification import EmailVerificationToken
from services.email_verification import (
    generate_verification_token,
    hash_verification_token,
)
from services.email import email_service



router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    if await get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    if await get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    hashed = hash_password(user.password)

    new_user = await create_user(
        db,
        user,
        hashed
    )

    # Генерируем токен подтверждения
    verification_token = generate_verification_token()

    token_hash = hash_verification_token(
        verification_token
    )

    verification = EmailVerificationToken(
        user_id=new_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )

    db.add(verification)

    await db.commit()

    # Отправляем письмо
    await email_service.send_verification_email(
        new_user.email,
        verification_token,
    )

    return {
        "message": "Registration successful. Please verify your email.",
        "username": new_user.username,
        "email": new_user.email,
    }


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
