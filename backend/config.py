# Loads settings from .env using pydantic-settings: ports, DB path, API key.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All backend configuration loaded from environment variables or .env."""

    API_KEY: str = 'dev-key-change-in-production'
    ADMIN_USERNAME: str = 'admin'
    ADMIN_PASSWORD: str = 'admin'
    SESSION_SECRET: str = 'dev-session-secret-change-in-production'
    SESSION_TTL_SECONDS: int = 12 * 60 * 60

    DATABASE_URL: str = 'sqlite+aiosqlite:///./data/database/honeypot.db'

    HONEYPOT_PORT: int = 8080
    HONEYPOT_HOST: str = '0.0.0.0'
    MANAGEMENT_HOST: str = '127.0.0.1'
    MANAGEMENT_PORT: int = 8000

    CORS_ORIGINS: str = 'http://localhost:5173,http://127.0.0.1:5173'
    EVENT_QUEUE_SIZE: int = 1000
    LOG_LEVEL: str = 'INFO'
    ENABLE_DECOY_PORTS: bool = False
    AUTH_RATE_LIMIT_PER_MINUTE: int = 20
    API_RATE_LIMIT_PER_MINUTE: int = 300

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(',') if o.strip()]


settings = Settings()
