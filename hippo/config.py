"""Configuration loaded from environment variables / .env file."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)

_BOT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


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
    hippo_whisper_model: str = "base"
    hippo_whisper_language: str | None = None  # e.g. "de", "en" — None = auto-detect
    hippo_embedding_model: str = "all-MiniLM-L6-v2"
    hippo_search_threshold: float = 0.4
    hippo_episodic_archive_days: int = 30
    hippo_retention_days: int = 90

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


def get_config(
    bot_name: str,
    _env_file: str | Path | None = ".env",
) -> HippoConfig:
    """Load configuration for the named bot.

    Env vars are resolved in priority order:
    1. ``{BOT_NAME}_*`` prefixed vars (per-bot overrides, e.g. ``ALICE_TELEGRAM_BOT_TOKEN``)
    2. Unprefixed vars (shared defaults / single-bot backward compatibility)

    Common settings like ``HIPPO_MODEL`` and ``HIPPO_TIMEZONE`` are read from the
    unprefixed fallback and can be overridden per-bot (e.g. ``ALICE_HIPPO_MODEL``).

    The ``_env_file`` parameter is intended for tests; pass ``None`` to skip
    reading the ``.env`` file entirely.
    """
    if not _BOT_NAME_RE.match(bot_name):
        msg = (
            f"Invalid bot name {bot_name!r}. "
            "Bot names must start with a letter and contain only "
            "letters, digits, and underscores."
        )
        raise ValueError(msg)

    prefix = f"{bot_name.upper()}_"
    env_file = _env_file

    class _BotConfig(HippoConfig):
        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            sources: tuple[PydanticBaseSettingsSource, ...] = (
                init_settings,
                EnvSettingsSource(settings_cls, env_prefix=prefix),
                EnvSettingsSource(settings_cls, env_prefix=""),
            )
            if env_file is not None:
                sources += (
                    DotEnvSettingsSource(settings_cls, env_file=env_file, env_prefix=prefix),
                    DotEnvSettingsSource(settings_cls, env_file=env_file, env_prefix=""),
                )
            sources += (file_secret_settings,)
            return sources

    return _BotConfig(hippo_bot_name=bot_name)  # type: ignore[call-arg]
