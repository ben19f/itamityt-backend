from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from core.config import settings


class S3Storage:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path",
                },
            ),
        )

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str,
    ) -> str:
        self.client.upload_fileobj(
            Fileobj=BytesIO(data),
            Bucket=settings.S3_BUCKET,
            Key=key,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

        return self.public_url(key)

    def delete(self, key: str) -> None:
        self.client.delete_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
        )

    def public_url(self, key: str) -> str:
        return f"{settings.S3_PUBLIC_URL.rstrip('/')}/{key}"

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(
                Bucket=settings.S3_BUCKET,
                Key=key,
            )
            return True
        except ClientError:
            return False


storage = S3Storage()