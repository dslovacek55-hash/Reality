from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://tracker:changeme@localhost:5432/realestate"
    database_url_sync: str = "postgresql://tracker:changeme@localhost:5432/realestate"
    redis_url: str = "redis://localhost:6379/0"

    sreality_interval_minutes: int = 30
    bezrealitky_interval_minutes: int = 120
    idnes_interval_minutes: int = 60

    # Email notifications (optional)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
