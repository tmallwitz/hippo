"""One-time vault setup — installs bundled assets on first run."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

# Bundled skills shipped with the hippo package
_ASSETS_DIR = Path(__file__).parent / "assets"


def setup_vault(vault_path: Path) -> None:
    """Ensure all expected vault directories exist and bundled skills are installed."""
    _create_vault_dirs(vault_path)
    _install_bundled_skills(vault_path)


def _create_vault_dirs(vault_path: Path) -> None:
    """Create standard vault subdirectories if they don't exist yet."""
    dirs = [
        "raw",
        "raw/processed",
        "personality",
    ]
    for d in dirs:
        (vault_path / d).mkdir(parents=True, exist_ok=True)


def _install_bundled_skills(vault_path: Path) -> None:
    """Copy bundled skills from the package into the vault's ``.claude/skills/`` folder.

    Skips any skill that is already installed (the skill's directory exists).
    This keeps skills up-to-date when the package is upgraded: delete the
    installed copy from the vault to force a reinstall on next startup.
    """
    skills_src = _ASSETS_DIR
    if not skills_src.is_dir():
        return

    skills_dst = vault_path / ".claude" / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)

    for skill_dir in skills_src.iterdir():
        if not skill_dir.is_dir():
            continue
        dst = skills_dst / skill_dir.name
        if dst.exists():
            log.debug("Skill '%s' already installed — skipping", skill_dir.name)
            continue
        shutil.copytree(skill_dir, dst)
        log.info("Installed bundled skill: %s → %s", skill_dir.name, dst)


# Keep old name as an alias so any existing callers still work
install_bundled_skills = setup_vault
