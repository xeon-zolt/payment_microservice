"""Import settings."""
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Implement base settings."""
    openapi_url: str = None
    docs_url: str = None
    redoc_url: str = None

    class Config:
        """Config class"""
        env_file = ".settings"


settings = Settings()
