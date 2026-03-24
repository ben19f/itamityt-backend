from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from db.crud_user import get_user_by_email
from db.deps import get_db
from models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()

    # кладем email (или username) в sub, чтобы get_current_user его мог прочитать
    if "sub" not in to_encode:
        to_encode["sub"] = data.get("email")  # или data.get("username")

    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
