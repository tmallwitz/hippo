"""Tests for HippoConfig loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from hippo.config import HippoConfig, get_config

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

    def test_phase6_defaults(self, tmp_path: Path) -> None:
        config = HippoConfig(
            telegram_bot_token="123:ABC",
            allowed_telegram_ids="111",
            hippo_vault_path=str(tmp_path),
            **_NO_ENV,
        )
        assert config.hippo_embedding_model == "all-MiniLM-L6-v2"
        assert config.hippo_search_threshold == 0.4
        assert config.hippo_episodic_archive_days == 30

    def test_phase6_overrides(self, tmp_path: Path) -> None:
        config = HippoConfig(
            telegram_bot_token="123:ABC",
            allowed_telegram_ids="111",
            hippo_vault_path=str(tmp_path),
            hippo_embedding_model="",
            hippo_search_threshold=0.6,
            hippo_episodic_archive_days=90,
            **_NO_ENV,
        )
        assert config.hippo_embedding_model == ""
        assert config.hippo_search_threshold == 0.6
        assert config.hippo_episodic_archive_days == 90


class TestMultiBotConfig:
    """Tests for get_config(bot_name) with per-bot env var prefixes."""

    def test_prefixed_env_vars(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """ALICE_ prefix vars are picked up for bot named Alice."""
        monkeypatch.setenv("ALICE_TELEGRAM_BOT_TOKEN", "alice-tok")
        monkeypatch.setenv("ALICE_ALLOWED_TELEGRAM_IDS", "111")
        monkeypatch.setenv("ALICE_HIPPO_VAULT_PATH", str(tmp_path))
        config = get_config("Alice")
        assert config.telegram_bot_token == "alice-tok"
        assert config.allowed_telegram_ids == [111]
        assert config.hippo_vault_path == tmp_path.resolve()
        assert config.hippo_bot_name == "Alice"

    def test_fallback_to_unprefixed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unprefixed vars work when no bot-specific prefix is set."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "generic-tok")
        monkeypatch.setenv("ALLOWED_TELEGRAM_IDS", "222")
        monkeypatch.setenv("HIPPO_VAULT_PATH", str(tmp_path))
        config = get_config("Generic")
        assert config.telegram_bot_token == "generic-tok"
        assert config.allowed_telegram_ids == [222]
        assert config.hippo_bot_name == "Generic"

    def test_prefixed_overrides_unprefixed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Per-bot ALICE_HIPPO_MODEL takes priority over shared HIPPO_MODEL."""
        monkeypatch.setenv("ALICE_TELEGRAM_BOT_TOKEN", "tok")
        monkeypatch.setenv("ALICE_ALLOWED_TELEGRAM_IDS", "111")
        monkeypatch.setenv("ALICE_HIPPO_VAULT_PATH", str(tmp_path))
        monkeypatch.setenv("HIPPO_MODEL", "shared-model")
        monkeypatch.setenv("ALICE_HIPPO_MODEL", "alice-model")
        config = get_config("Alice")
        assert config.hippo_model == "alice-model"

    def test_shared_model_without_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shared HIPPO_MODEL applies when bot has no per-bot override."""
        monkeypatch.setenv("BOB_TELEGRAM_BOT_TOKEN", "bob-tok")
        monkeypatch.setenv("BOB_ALLOWED_TELEGRAM_IDS", "333")
        monkeypatch.setenv("BOB_HIPPO_VAULT_PATH", str(tmp_path))
        monkeypatch.setenv("HIPPO_MODEL", "shared-model")
        config = get_config("Bob")
        assert config.hippo_model == "shared-model"

    def test_two_bots_independent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Two get_config() calls produce independent configs from the same env."""
        vault_a = tmp_path / "alice"
        vault_a.mkdir()
        vault_b = tmp_path / "bob"
        vault_b.mkdir()
        monkeypatch.setenv("ALICE_TELEGRAM_BOT_TOKEN", "a-tok")
        monkeypatch.setenv("ALICE_ALLOWED_TELEGRAM_IDS", "111")
        monkeypatch.setenv("ALICE_HIPPO_VAULT_PATH", str(vault_a))
        monkeypatch.setenv("BOB_TELEGRAM_BOT_TOKEN", "b-tok")
        monkeypatch.setenv("BOB_ALLOWED_TELEGRAM_IDS", "222")
        monkeypatch.setenv("BOB_HIPPO_VAULT_PATH", str(vault_b))
        ca = get_config("Alice")
        cb = get_config("Bob")
        assert ca.telegram_bot_token != cb.telegram_bot_token
        assert ca.hippo_vault_path != cb.hippo_vault_path
        assert ca.hippo_bot_name == "Alice"
        assert cb.hippo_bot_name == "Bob"

    def test_missing_required_vars_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config fails fast with ValidationError if required vars are absent."""
        # Clear any vars that might bleed in from the real environment
        ghost_vars = (
            "TELEGRAM_BOT_TOKEN",
            "ALLOWED_TELEGRAM_IDS",
            "HIPPO_VAULT_PATH",
            "GHOST_TELEGRAM_BOT_TOKEN",
            "GHOST_ALLOWED_TELEGRAM_IDS",
            "GHOST_HIPPO_VAULT_PATH",
        )
        for var in ghost_vars:
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ValidationError):
            get_config("Ghost", _env_file=None)

    def test_invalid_bot_name_rejected(self) -> None:
        """Bot names with special characters are rejected before config loading."""
        with pytest.raises(ValueError, match="Invalid bot name"):
            get_config("alice-bot")

    def test_invalid_bot_name_starts_with_digit(self) -> None:
        """Bot names starting with a digit are rejected."""
        with pytest.raises(ValueError, match="Invalid bot name"):
            get_config("1alice")
