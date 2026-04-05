"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault directory with memory subfolders."""
    (tmp_path / "semantic").mkdir()
    (tmp_path / "episodic").mkdir()
    (tmp_path / "scheduled").mkdir()
    (tmp_path / "short_term").mkdir()
    (tmp_path / "short_term" / "processed").mkdir()
    (tmp_path / "inbox").mkdir()
    (tmp_path / "dream_reports").mkdir()
    return tmp_path
