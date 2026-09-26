import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from core.config import settings
from services.storage import storage


router = APIRouter(
    prefix="/storage-test",
    tags=["storage-test"],
)


@router.post("/upload")
async def upload_test_file(
    file: UploadFile = File(...),
):
    try:
        data = await file.read()

        key = (
            f"{settings.S3_PREFIX}/"
            f"test/"
            f"{uuid.uuid4()}-{file.filename}"
        )

        url = storage.upload_bytes(
            data=data,
            key=key,
            content_type=file.content_type or "application/octet-stream",
        )

        return {
            "success": True,
            "key": key,
            "url": url,
            "size": len(data),
            "content_type": file.content_type,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"S3 upload failed: {exc}",
        )