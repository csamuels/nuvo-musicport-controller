"""API configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # NuVo Device
    nuvo_host: str = "10.0.0.45"
    nuvo_port: int = 5006

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: list = ["*"]  # For development - restrict in production

    class Config:
        env_file = ".env"


settings = Settings()
