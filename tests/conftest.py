"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault directory with semantic/ and episodic/ subfolders."""
    (tmp_path / "semantic").mkdir()
    (tmp_path / "episodic").mkdir()
    return tmp_path
