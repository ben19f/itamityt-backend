from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from core.config import settings


class S3Storage:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path",
                },
            ),
        )

    async def upload_file(
        self,
        file: UploadFile,
        key: str,
        content_type: str | None = None,
    ) -> str:
        file_object = file.file

        file_object.seek(0)

        await run_in_threadpool(
            self.client.upload_fileobj,
            file_object,
            settings.s3_bucket,
            key,
            ExtraArgs={
                "ContentType": (
                    content_type
                    or file.content_type
                    or "application/octet-stream"
                ),
            },
        )

        return self.public_url(key)

    async def delete(self, key: str) -> None:
        await run_in_threadpool(
            self.client.delete_object,
            Bucket=settings.s3_bucket,
            Key=key,
        )

    async def exists(self, key: str) -> bool:
        try:
            await run_in_threadpool(
                self.client.head_object,
                Bucket=settings.s3_bucket,
                Key=key,
            )
            return True

        except ClientError:
            return False

    def public_url(self, key: str) -> str:
        return (
            f"{settings.s3_public_url.rstrip('/')}/"
            f"{key.lstrip('/')}"
        )

    def key_from_url(self, url: str) -> str | None:
        prefix = settings.s3_public_url.rstrip("/") + "/"

        if not url.startswith(prefix):
            return None

        return url[len(prefix):]


storage = S3Storage()