from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    S3_ENDPOINT: str
    S3_PUBLIC_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str
    S3_REGION: str = "us-east-1"
    S3_PREFIX: str = "dev"

    MAX_AVATAR_SIZE: int = 5 * 1024 * 1024
    MAX_PHOTO_SIZE: int = 10 * 1024 * 1024
    MAX_USER_PHOTOS: int = 5

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()