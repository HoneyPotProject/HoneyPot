# Loads all settings from .env. No defaults: a missing value stops startup.

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / '.env'


class Settings(BaseSettings):
    API_KEY: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    SESSION_SECRET: str
    SESSION_TTL_SECONDS: int

    DATABASE_URL: str

    HONEYPOT_HOST: str
    HONEYPOT_PORT: int
    MANAGEMENT_HOST: str
    MANAGEMENT_PORT: int

    CORS_ORIGINS: str
    EVENT_QUEUE_SIZE: int
    LOG_LEVEL: str
    ENABLE_DECOY_PORTS: bool
    AUTH_RATE_LIMIT_PER_MINUTE: int
    API_RATE_LIMIT_PER_MINUTE: int

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    @model_validator(mode='after')
    def _reject_placeholders(self):
        for name in ('API_KEY', 'ADMIN_PASSWORD', 'SESSION_SECRET'):
            value = getattr(self, name)
            if value.lower().startswith(('change', 'dev-')) or value.lower() == 'admin':
                raise ValueError(f'{name} in .env is still a placeholder')
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(',') if o.strip()]


settings = Settings()