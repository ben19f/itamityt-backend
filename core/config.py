from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # База данных
    database_url: str

    # JWT / auth
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # Настройка чтения .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",  # можно поставить "ITAMITYT_" если хочешь префиксы
        env_names={
            "database_url": "DATABASE_URL",
            "secret_key": "SECRET_KEY",
            "algorithm": "ALGORITHM",
            "access_token_expire_minutes": "ACCESS_TOKEN_EXPIRE_MINUTES",
        },
    )

settings = Settings()
