"""Tests for the __main__ CLI argument parsing."""

from __future__ import annotations

import subprocess
import sys


class TestCLIArgs:
    def test_missing_bot_name_exits_nonzero(self) -> None:
        """Running `hippo` without a bot name argument must exit non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "hippo"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0

    def test_missing_bot_name_prints_usage(self) -> None:
        """The error output should mention the missing argument."""
        result = subprocess.run(
            [sys.executable, "-m", "hippo"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        combined = (result.stdout + result.stderr).lower()
        # argparse prints "error:" and the argument name in the usage message
        assert "error" in combined or "usage" in combined

    def test_invalid_bot_name_rejected(self) -> None:
        """A bot name with a hyphen must be rejected before touching config."""
        result = subprocess.run(
            [sys.executable, "-m", "hippo", "bad-name"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "bad-name" in combined or "error" in combined.lower()

    def test_help_flag_works(self) -> None:
        """--help must exit 0 and print usage."""
        result = subprocess.run(
            [sys.executable, "-m", "hippo", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        stdout_lower = result.stdout.lower()
        assert "bot_name" in result.stdout or "BotName" in result.stdout or "usage" in stdout_lower
