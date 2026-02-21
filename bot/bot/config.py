from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    telegram_bot_token: str = ""
    database_url: str = "postgresql+asyncpg://tracker:changeme@localhost:5432/realestate"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


bot_settings = BotSettings()
