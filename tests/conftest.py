"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault directory with a semantic/ subfolder."""
    semantic = tmp_path / "semantic"
    semantic.mkdir()
    return tmp_path
