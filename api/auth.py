from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.deps import get_db
from schemas.user import UserCreate, UserLogin
from db.crud_user import (
    get_user_by_email,
    get_user_by_username,
    create_user
)

from core.security import hash_password, verify_password, create_access_token

from models.email_verification import EmailVerificationToken
from services.email_verification import (
    generate_verification_token,
    hash_verification_token,
)
from services.email import email_service
from models.users_model import User



router = APIRouter(prefix="/auth", tags=["auth"])


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


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


@router.post("/password-reset/request")
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a reset link only for an existing account with verified email."""

    email = str(data.email)
    result = await db.execute(
        select(User).where(
            User.email == email,
            User.email_verified.is_(True),
        )
    )
    user = result.scalar_one_or_none()

    if user is not None:
        result = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.purpose == "password_reset",
            )
        )
        for old_token in result.scalars():
            await db.delete(old_token)

        raw_token = generate_verification_token()
        db.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hash_verification_token(raw_token),
                purpose="password_reset",
                expires_at=datetime.utcnow() + timedelta(hours=1),
            )
        )
        await db.commit()
        await email_service.send_password_reset_email(email, raw_token)

    # Keep the response the same whether the address exists or is verified.
    return {
        "message": "Если адрес подтверждён и зарегистрирован, на него отправлена ссылка для сброса пароля"
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    token_hash = hash_verification_token(data.token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.purpose == "password_reset",
        )
    )
    reset_token = result.scalar_one_or_none()

    if reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ссылка недействительна или уже использована",
        )

    if reset_token.expires_at < datetime.utcnow():
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Срок действия ссылки истёк",
        )

    user = await db.get(User, reset_token.user_id)
    if user is None or not user.email_verified:
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сброс пароля недоступен для этого аккаунта",
        )

    user.hashed_password = hash_password(data.new_password)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.purpose == "password_reset",
        )
    )
    for user_token in result.scalars():
        await db.delete(user_token)

    await db.commit()
    return {"message": "Пароль успешно изменён"}
