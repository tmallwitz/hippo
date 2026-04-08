---
name: bundled-assets
description: Ship reusable assets in hippo/assets/ and copy them to the vault on startup if not already installed.
type: pattern
needs_review: false
auto_promoted_from: agent-os/specs/2026-04-05-phase4-dream-completion
---

# Bundled Assets Pattern

Assets that need to exist in the vault (skills, templates, reference docs) are shipped inside the Python package at `hippo/assets/` and installed into the vault on first startup.

```python
def _install_bundled_skills(vault_path: Path) -> None:
    skills_src = Path(__file__).parent / "assets"
    skills_dst = vault_path / ".claude" / "skills"
    for skill_dir in skills_src.iterdir():
        dst = skills_dst / skill_dir.name
        if dst.exists():
            continue  # already installed
        shutil.copytree(skill_dir, dst)
```

**Rules:**
- Skip installation if the target directory already exists (user may have customized it).
- To force a reinstall, the user deletes the installed copy from the vault.
- Never download assets from the network at runtime — bundle them in the package.
- `hippo/setup.py` runs on every startup; keep it idempotent and fast.
