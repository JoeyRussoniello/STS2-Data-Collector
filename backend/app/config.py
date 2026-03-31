from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost:5432/sts2"
    steam_id_salt: str = "change-me-in-production"

    model_config = {"env_prefix": "STS2_", "env_file": ".env"}


settings = Settings()
