# Loads settings from .env using pydantic-settings: ports, DB path, API key.

from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """
    All backend configuration loaded from environment variables or .env file.

    pydantic-settings automatically reads from .env if python-dotenv is installed.
    """

    # Authentication: management API key.
    # Clients send this as: X-API-Key: <value>
    API_KEY: str = 'dev-key-change-in-production'

    # SQLite database URL.
    # Format: sqlite+aiosqlite:///./data/database/honeypot.db
    DATABASE_URL: str = 'sqlite+aiosqlite:///./data/database/honeypot.db'

    # Port the decoy HTTP honeypot listens on.
    HONEYPOT_PORT: int = 8080

    # Port the FastAPI management API listens on.
    MANAGEMENT_PORT: int = 8000

    # Allowed CORS origins (browser can call the API from these origins).
    CORS_ORIGINS: str = 'http://localhost:5173,http://127.0.0.1:5173'

    # Maximum events in the in-memory queue before we start dropping.
    EVENT_QUEUE_SIZE: int = 1000

    # Python logging level.
    LOG_LEVEL: str = 'INFO'

    @property
    def cors_origins_list(self) -> list:
        """Split the comma-separated CORS string into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(',') if o.strip()]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'


# Single shared instance used throughout the backend.
settings = Settings()
