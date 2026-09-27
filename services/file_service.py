from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from core.config import settings

# ============================================================
# Разрешенные изображения
# ============================================================

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


# ============================================================
# Пути
# ============================================================

def get_images_root() -> Path:
    return Path(settings.USERS_IMAGES_DIR)


def get_avatar_dir(user_id: int) -> Path:
    return (
            get_images_root()
            / "avatars"
            / str(user_id)
    )


def get_photos_dir(user_id: int) -> Path:
    return (
            get_images_root()
            / "photos"
            / str(user_id)
    )


# ============================================================
# Проверка изображения
# ============================================================

def get_image_extension(file: UploadFile) -> str:
    extension = ALLOWED_IMAGE_TYPES.get(
        file.content_type
    )

    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Разрешены только JPEG, PNG и WEBP",
        )

    return extension


async def read_image(
        file: UploadFile,
        max_size: int,
) -> bytes:
    extension = get_image_extension(file)

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл пустой",
        )

    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл слишком большой",
        )

    return content


# ============================================================
# Сохранение
# ============================================================

async def save_avatar(
        user_id: int,
        file: UploadFile,
) -> tuple[Path, str]:
    """
    Сохраняет аватар.

    Возвращает:
        filesystem_path
        public_url
    """

    extension = get_image_extension(file)

    content = await read_image(
        file,
        settings.MAX_AVATAR_SIZE,
    )

    directory = get_avatar_dir(user_id)

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"{uuid4().hex}{extension}"

    filesystem_path = directory / filename

    filesystem_path.write_bytes(content)

    public_url = (
        f"{settings.USERS_IMAGES_URL}"
        f"/avatars/{user_id}/{filename}"
    )

    return filesystem_path, public_url


async def save_photo(
        user_id: int,
        file: UploadFile,
) -> tuple[Path, str]:
    """
    Сохраняет фотографию пользователя.

    Возвращает:
        filesystem_path
        public_url
    """

    extension = get_image_extension(file)

    content = await read_image(
        file,
        settings.MAX_PHOTO_SIZE,
    )

    directory = get_photos_dir(user_id)

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"{uuid4().hex}{extension}"

    filesystem_path = directory / filename

    filesystem_path.write_bytes(content)

    public_url = (
        f"{settings.USERS_IMAGES_URL}"
        f"/photos/{user_id}/{filename}"
    )

    return filesystem_path, public_url


# ============================================================
# Удаление
# ============================================================

def delete_file(
        filesystem_path: Path | None,
) -> None:
    """
    Удаляет файл с диска.

    Если файла уже нет — ничего не делает.
    """

    if not filesystem_path:
        return

    if filesystem_path.exists() and filesystem_path.is_file():
        filesystem_path.unlink()


# ============================================================
# Public URL -> filesystem path
# ============================================================

def public_url_to_path(
        public_url: str | None,
) -> Path | None:
    """
    Преобразует URL изображения из БД
    обратно в физический путь.

    Например:

    /images/users_images/avatars/15/abc.jpg

    ->

    /var/www/html/images/users_images/avatars/15/abc.jpg
    """

    if not public_url:
        return None

    base_url = settings.USERS_IMAGES_URL.rstrip("/")
    url = public_url.rstrip("/")

    if not url.startswith(base_url + "/"):
        return None

    relative_path = url[
        len(base_url) + 1:
    ]

    root = get_images_root().resolve()

    file_path = (
            root / relative_path
    ).resolve()

    # Защита от выхода за пределы USERS_IMAGES_DIR
    try:
        file_path.relative_to(root)
    except ValueError:
        return None

    return file_path