from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar()


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar()


async def get_last_users(db: AsyncSession, limit: int = 3):
    result = await db.execute(
        select(User).order_by(User.id.desc()).limit(limit)
    )
    return result.scalars().all()


async def create_user(db: AsyncSession, user: UserCreate, hashed_password: str):

    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def delete_user_by_id(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    if not user:
        return
    await db.delete(user)
    await db.commit()
