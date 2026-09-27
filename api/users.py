import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import get_current_user, hash_password
from db.crud_user import delete_user_by_id
from db.deps import get_db
# from models.user_photo import UserPhoto
from models.users_model import User, UserPhoto
from services.storage import storage

from datetime import datetime

from models.email_verification import EmailVerificationToken
from services.email_verification import hash_verification_token



router = APIRouter(prefix="/users", tags=["users"])


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class EmailVerificationRequest(BaseModel):
    token: str

class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    profile_description: str | None = None
    profile_extra_info: str | None = None


async def validate_image(
    file: UploadFile,
    max_size: int,
) -> str:
    """
    Проверяет тип и размер изображения.

    Возвращает расширение файла:
    jpg / png / webp
    """

    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content-Type is required",
        )

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Allowed: JPEG, PNG, WEBP",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File is too large. "
                f"Maximum size is {max_size // 1024 // 1024} MB"
            ),
        )

    return ALLOWED_IMAGE_TYPES[file.content_type]


@router.post("/verify-email")
async def verify_email(
    data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    token_hash = hash_verification_token(data.token)

    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )

    verification_token = result.scalar_one_or_none()

    if verification_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    if verification_token.expires_at < datetime.utcnow():
        await db.delete(verification_token)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired",
        )

    result = await db.execute(
        select(User).where(
            User.id == verification_token.user_id
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.email_verified = True

    # Токен одноразовый
    await db.delete(verification_token)

    await db.commit()

    return {
        "message": "Email successfully verified",
        "email_verified": True,
    }



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
    }


@router.patch("/me")
async def update_me(
    profile: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = profile.model_dump(exclude_unset=True)

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
    }


@router.get("/me/photos")
async def get_my_photos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPhoto)
        .where(UserPhoto.user_id == current_user.id)
        .order_by(UserPhoto.position)
    )

    photos = result.scalars().all()

    return [
        {
            "id": photo.id,
            "image_url": photo.image_url,
            "position": photo.position,
        }
        for photo in photos
    ]

@router.post("/register", status_code=status.HTTP_201_CREATED)
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

    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )

    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
    }


@router.delete(
    "/delete/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_user_by_id(
        db=db,
        user_id=current_user.id,
    )


@router.delete(
    "/delete/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    extension = await validate_image(
        file,
        settings.max_avatar_size,
    )

    key = (
        f"{settings.s3_prefix}/"
        f"users/avatars/"
        f"{current_user.id}/"
        f"{uuid.uuid4()}.{extension}"
    )

    old_avatar_url = current_user.avatar_url

    try:
        avatar_url = await storage.upload_file(
            file=file,
            key=key,
            content_type=file.content_type,
        )

        current_user.avatar_url = avatar_url

        await db.commit()
        await db.refresh(current_user)

    except Exception:
        try:
            await storage.delete(key)
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar",
        )

    # Удаляем старый файл после успешного сохранения нового
    if old_avatar_url:
        old_key = storage.key_from_url(old_avatar_url)

        if old_key:
            try:
                await storage.delete(old_key)
            except Exception:
                pass

    return {
        "avatar_url": current_user.avatar_url,
    }


@router.delete(
    "/me/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.avatar_url:
        return

    avatar_url = current_user.avatar_url
    avatar_key = storage.key_from_url(avatar_url)

    current_user.avatar_url = None

    await db.commit()

    if avatar_key:
        try:
            await storage.delete(avatar_key)
        except Exception:
            pass


@router.post("/me/photos")
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPhoto)
        .where(UserPhoto.user_id == current_user.id)
        .order_by(UserPhoto.position)
    )

    photos = result.scalars().all()

    if len(photos) >= settings.max_user_photos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Maximum number of photos is "
                f"{settings.max_user_photos}"
            ),
        )

    extension = await validate_image(
        file,
        settings.max_photo_size,
    )

    position = len(photos)

    key = (
        f"{settings.s3_prefix}/"
        f"users/photos/"
        f"{current_user.id}/"
        f"{uuid.uuid4()}.{extension}"
    )

    try:
        image_url = await storage.upload_file(
            file=file,
            key=key,
            content_type=file.content_type,
        )

        photo = UserPhoto(
            user_id=current_user.id,
            image_url=image_url,
            position=position,
        )

        db.add(photo)

        await db.commit()
        await db.refresh(photo)

    except Exception:
        try:
            await storage.delete(key)
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload photo",
        )

    return {
        "id": photo.id,
        "image_url": photo.image_url,
        "position": photo.position,
    }


@router.delete(
    "/me/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
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

    photo = result.scalar_one_or_none()

    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )

    image_url = photo.image_url
    image_key = storage.key_from_url(image_url)

    await db.delete(photo)
    await db.commit()

    if image_key:
        try:
            await storage.delete(image_key)
        except Exception:
            pass



