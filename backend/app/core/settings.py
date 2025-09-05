# backend/app/core/settings.py
from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, model_validator


_THIS_DIR = os.path.dirname(__file__)
_DOTENV_PATH = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".env"))
load_dotenv(_DOTENV_PATH, override=False)
load_dotenv(override=False) 


class Settings(BaseModel):
    
    env: Literal["dev", "prod", "test"]
    database_url: str  

    # Tunables (safe defaults)
    short_code_length: int = 7
    rate_limit_per_min: int = 60

    @field_validator("short_code_length")
    @classmethod
    def validate_short_code_length(cls, v: int) -> int:
        if not (3 <= v <= 32):
            raise ValueError("SHORT_CODE_LENGTH must be between 3 and 32")
        return v

    @field_validator("rate_limit_per_min")
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        if v < 1:
            raise ValueError("RATE_LIMIT_PER_MIN must be >= 1")
        return v

    @model_validator(mode="after")
    def validate_environment_rules(self) -> "Settings":
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")
        if self.env == "prod" and self.database_url.startswith("sqlite"):
            raise ValueError("SQLite is not allowed in ENV=prod; use a network DB (e.g., Postgres)")
        return self


def _getenv_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


def load_settings() -> Settings:
    return Settings(
        env=os.getenv("ENV", "dev"),
        database_url=os.getenv("DATABASE_URL", ""),  
        short_code_length=_getenv_int("SHORT_CODE_LENGTH", 7),
        rate_limit_per_min=_getenv_int("RATE_LIMIT_PER_MIN", 60),
    )


# Import this in the app: from app.core.settings import settings
settings: Settings = load_settings()

if __name__ == "__main__":
    # Dev-only check (avoid printing secrets in real logs)
    print(settings.model_dump())
