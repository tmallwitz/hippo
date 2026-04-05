"""Tests for HippoConfig loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from hippo.config import HippoConfig

# _env_file=None prevents reading the real .env during tests
_NO_ENV = {"_env_file": None}


class TestConfigParsing:
    def test_valid_config(self, tmp_path: Path) -> None:
        config = HippoConfig(
            telegram_bot_token="123:ABC",
            allowed_telegram_ids="111,222,333",
            hippo_vault_path=str(tmp_path),
            **_NO_ENV,
        )
        assert config.telegram_bot_token == "123:ABC"
        assert config.allowed_telegram_ids == [111, 222, 333]
        assert config.hippo_vault_path == tmp_path.resolve()
        assert config.hippo_bot_name == "alice"
        assert config.hippo_model == "claude-sonnet-4-5"

    def test_single_id(self, tmp_path: Path) -> None:
        config = HippoConfig(
            telegram_bot_token="123:ABC",
            allowed_telegram_ids="42",
            hippo_vault_path=str(tmp_path),
            **_NO_ENV,
        )
        assert config.allowed_telegram_ids == [42]

    def test_missing_token_fails(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            HippoConfig(
                allowed_telegram_ids="111",
                hippo_vault_path=str(tmp_path),
                **_NO_ENV,
            )

    def test_empty_ids_fails(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="at least one ID"):
            HippoConfig(
                telegram_bot_token="123:ABC",
                allowed_telegram_ids="",
                hippo_vault_path=str(tmp_path),
                **_NO_ENV,
            )

    def test_nonexistent_vault_fails(self) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            HippoConfig(
                telegram_bot_token="123:ABC",
                allowed_telegram_ids="111",
                hippo_vault_path="/nonexistent/path/that/does/not/exist",
                **_NO_ENV,
            )

    def test_custom_model(self, tmp_path: Path) -> None:
        config = HippoConfig(
            telegram_bot_token="123:ABC",
            allowed_telegram_ids="111",
            hippo_vault_path=str(tmp_path),
            hippo_model="claude-opus-4-1-20250805",
            **_NO_ENV,
        )
        assert config.hippo_model == "claude-opus-4-1-20250805"

    def test_dream_model_default(self, tmp_path: Path) -> None:
        config = HippoConfig(
            telegram_bot_token="123:ABC",
            allowed_telegram_ids="111",
            hippo_vault_path=str(tmp_path),
            **_NO_ENV,
        )
        assert config.hippo_dream_model == "claude-sonnet-4-5"

    def test_custom_dream_model(self, tmp_path: Path) -> None:
        config = HippoConfig(
            telegram_bot_token="123:ABC",
            allowed_telegram_ids="111",
            hippo_vault_path=str(tmp_path),
            hippo_dream_model="claude-haiku-4-5-20251001",
            **_NO_ENV,
        )
        assert config.hippo_dream_model == "claude-haiku-4-5-20251001"
