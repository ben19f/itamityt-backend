from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import (
    hash_password,
    get_current_user,
)

from models.users_model import (
    User,
    UserPhoto,
)

from db.deps import get_db
from db.crud_user import delete_user_by_id

from services.file_service import (
    delete_file,
    public_url_to_path,
    save_avatar,
    save_photo,
)

from core.config import settings


router = APIRouter(
    prefix="/users",
    tags=["users"],
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


# ============================================================
# GET /users/me
# ============================================================

@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
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
    db: AsyncSession = Depends(get_db),
):
    data = profile.model_dump(
        exclude_unset=True,
    )

    for field, value in data.items():
        setattr(
            current_user,
            field,
            value,
        )

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
# POST /users/me/avatar
#
# Загрузка / замена аватара
# ============================================================

@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    old_avatar_url = current_user.avatar_url

    new_file_path = None

    try:
        new_file_path, new_avatar_url = await save_avatar(
            current_user.id,
            file,
        )

        current_user.avatar_url = new_avatar_url

        await db.commit()
        await db.refresh(current_user)

    except HTTPException:
        if new_file_path:
            delete_file(new_file_path)

        await db.rollback()
        raise

    except Exception:
        if new_file_path:
            delete_file(new_file_path)

        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить аватар",
        )

    # Старый файл удаляем только после успешного commit.
    if old_avatar_url:
        old_file_path = public_url_to_path(
            old_avatar_url
        )

        delete_file(old_file_path)

    return {
        "avatar_url": current_user.avatar_url,
    }


# ============================================================
# DELETE /users/me/avatar
#
# Удаление аватара
# ============================================================

@router.delete("/me/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аватар отсутствует",
        )

    avatar_url = current_user.avatar_url

    current_user.avatar_url = None

    await db.commit()

    avatar_path = public_url_to_path(
        avatar_url
    )

    delete_file(avatar_path)

    return {
        "avatar_url": None,
    }


# ============================================================
# POST /users/me/photos
#
# Добавление фотографии
# ============================================================

@router.post("/me/photos")
async def upload_photo(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPhoto).where(
            UserPhoto.user_id == current_user.id
        )
    )

    photos = result.scalars().all()

    if len(photos) >= settings.MAX_USER_PHOTOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Можно загрузить максимум "
                f"{settings.MAX_USER_PHOTOS} фотографий"
            ),
        )

    new_file_path = None

    try:
        new_file_path, image_url = await save_photo(
            current_user.id,
            file,
        )

        position = len(photos)

        photo = UserPhoto(
            user_id=current_user.id,
            image_url=image_url,
            position=position,
        )

        db.add(photo)

        await db.commit()
        await db.refresh(photo)

    except HTTPException:
        if new_file_path:
            delete_file(new_file_path)

        await db.rollback()
        raise

    except Exception:
        if new_file_path:
            delete_file(new_file_path)

        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить фотографию",
        )

    return {
        "id": photo.id,
        "image_url": photo.image_url,
        "position": photo.position,
    }


# ============================================================
# DELETE /users/me/photos/{photo_id}
#
# Удаление фотографии
# ============================================================

@router.delete("/me/photos/{photo_id}")
async def delete_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPhoto).where(
            UserPhoto.id == photo_id,
            UserPhoto.user_id == current_user.id,
        )
    )

    photo = result.scalars().first()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена",
        )

    image_url = photo.image_url

    await db.delete(photo)

    await db.commit()

    image_path = public_url_to_path(
        image_url
    )

    delete_file(image_path)

    return {
        "id": photo_id,
        "deleted": True,
    }


# ============================================================
# POST /users/register
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            (User.username == user.username)
            | (User.email == user.email)
        )
    )

    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(
            user.password
        ),
    )

    db.add(db_user)

    await db.commit()
    await db.refresh(db_user)

    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
    }


# ============================================================
# DELETE /users/delete/me
# ============================================================

@router.delete(
    "/delete/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_user_by_id(
        db,
        current_user.id,
    )

    return


# ============================================================
# DELETE /users/delete/{user_id}
# ============================================================

@router.delete(
    "/delete/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.id == user_id
        )
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)

    await db.commit()

    return