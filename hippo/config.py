"""Configuration loaded from environment variables / .env file."""

from __future__ import annotations

import functools
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


class HippoConfig(BaseSettings):
    """Hippo bot configuration. All values come from environment or .env."""

    model_config = {"env_prefix": "", "env_file": ".env", "env_file_encoding": "utf-8"}

    telegram_bot_token: str
    allowed_telegram_ids: list[int]
    hippo_vault_path: Path
    hippo_bot_name: str = "alice"
    hippo_model: str = "claude-sonnet-4-5"
    hippo_dream_model: str = "claude-sonnet-4-5"
    hippo_timezone: str = "Europe/Berlin"
    hippo_buffer_max_entries: int = 50

    @field_validator("allowed_telegram_ids", mode="before")
    @classmethod
    def parse_comma_separated_ids(cls, v: object) -> list[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            if not parts:
                msg = "ALLOWED_TELEGRAM_IDS must contain at least one ID"
                raise ValueError(msg)
            return [int(p) for p in parts]
        if isinstance(v, list):
            return [int(i) for i in v]
        msg = f"Expected comma-separated string or list, got {type(v)}"
        raise TypeError(msg)

    @field_validator("hippo_vault_path")
    @classmethod
    def validate_vault_path(cls, v: Path) -> Path:
        resolved = v.resolve()
        if not resolved.is_dir():
            msg = f"HIPPO_VAULT_PATH does not exist or is not a directory: {resolved}"
            raise ValueError(msg)
        return resolved


@functools.lru_cache(maxsize=1)
def get_config() -> HippoConfig:
    """Load and cache the configuration singleton."""
    return HippoConfig()  # type: ignore[call-arg]
