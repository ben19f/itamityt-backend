from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # S3
    s3_endpoint: str
    s3_public_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    s3_region: str = "us-east-1"
    s3_prefix: str = "dev"

    # Upload limits
    max_avatar_size: int = 5 * 1024 * 1024
    max_photo_size: int = 10 * 1024 * 1024
    max_user_photos: int = 5

    model_config = SettingsConfigDict(
        extra="ignore"
    )


settings = Settings()