"""Dream cycle housekeeping — prunes old vault files and consolidates episodic archives."""

from __future__ import annotations

import contextlib
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import frontmatter

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_housekeeping(vault_path: Path, retention_days: int) -> dict[str, int]:
    """Prune old files and consolidate episodic archives.

    Blocking — run via ``asyncio.to_thread`` from the dream runner.

    Returns a dict with counts of what was cleaned up:
    - buffer_archives_pruned
    - dream_reports_pruned
    - completed_tasks_pruned
    - raw_processed_pruned
    - archive_months_consolidated
    """
    cutoff = date.today() - timedelta(days=retention_days)

    stats: dict[str, int] = {
        "buffer_archives_pruned": 0,
        "dream_reports_pruned": 0,
        "completed_tasks_pruned": 0,
        "raw_processed_pruned": 0,
        "archive_months_consolidated": 0,
    }

    stats["buffer_archives_pruned"] = _prune_dated_files(
        vault_path / "short_term" / "processed", "*.md", cutoff
    )
    stats["dream_reports_pruned"] = _prune_dated_files(
        vault_path / "dream_reports", "*.md", cutoff
    )
    stats["completed_tasks_pruned"] = _prune_completed_tasks(vault_path / "scheduled", cutoff)
    stats["raw_processed_pruned"] = _prune_by_mtime(vault_path / "raw" / "processed", cutoff)
    stats["archive_months_consolidated"] = _consolidate_episodic_archives(
        vault_path / "episodic" / "archive"
    )

    return stats


# ---------------------------------------------------------------------------
# Pruning helpers
# ---------------------------------------------------------------------------


def _prune_dated_files(directory: Path, pattern: str, cutoff: date) -> int:
    """Delete files whose stem is a YYYY-MM-DD date older than cutoff.

    Returns count deleted.
    """
    if not directory.is_dir():
        return 0
    count = 0
    for path in directory.glob(pattern):
        try:
            file_date = date.fromisoformat(path.stem)
        except ValueError:
            continue  # not a dated file — skip
        if file_date < cutoff:
            try:
                path.unlink()
                count += 1
                log.debug("Housekeeping: deleted %s", path)
            except OSError:
                log.warning("Housekeeping: could not delete %s", path)
    return count


def _prune_by_mtime(directory: Path, cutoff: date) -> int:
    """Delete all files under directory whose mtime is before cutoff.

    Recurses into subdirectories. Empty directories are removed.
    Returns count of files deleted.
    """
    if not directory.is_dir():
        return 0
    count = 0
    cutoff_ts = datetime.combine(cutoff, datetime.min.time()).timestamp()
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        try:
            if path.stat().st_mtime < cutoff_ts:
                path.unlink()
                count += 1
                log.debug("Housekeeping: deleted %s", path)
        except OSError:
            log.warning("Housekeeping: could not delete %s", path)

    # Remove empty subdirectories (bottom-up)
    for path in sorted(directory.rglob("*"), reverse=True):
        if path.is_dir():
            with contextlib.suppress(OSError):
                path.rmdir()  # only succeeds if empty

    return count


def _prune_completed_tasks(scheduled_dir: Path, cutoff: date) -> int:
    """Delete completed task files whose creation date is before cutoff.

    Leaves pending and active tasks untouched.
    Returns count deleted.
    """
    if not scheduled_dir.is_dir():
        return 0
    count = 0
    for path in scheduled_dir.glob("task-*.md"):
        try:
            post = frontmatter.load(str(path))
            if post.metadata.get("status") != "completed":
                continue
            raw_created = post.metadata.get("created", "")
            # created is an ISO datetime string
            created_date = datetime.fromisoformat(str(raw_created)).date()
            if created_date < cutoff:
                path.unlink()
                count += 1
                log.debug("Housekeeping: deleted completed task %s", path.name)
        except Exception:
            log.warning("Housekeeping: could not process task file %s", path.name)
    return count


# ---------------------------------------------------------------------------
# Episodic archive consolidation
# ---------------------------------------------------------------------------


def _consolidate_episodic_archives(archive_dir: Path) -> int:
    """Merge daily YYYY-MM-DD.md files into monthly YYYY-MM.md files.

    Only processes months strictly before the current month.
    Daily files are deleted after successful consolidation.
    Returns count of months consolidated.
    """
    if not archive_dir.is_dir():
        return 0

    today = date.today()
    current_month = today.strftime("%Y-%m")

    # Group daily files by month
    by_month: dict[str, list[Path]] = defaultdict(list)
    for path in archive_dir.glob("*.md"):
        # Skip already-consolidated monthly files (stem is YYYY-MM, 7 chars)
        if len(path.stem) == 7:
            continue
        try:
            file_date = date.fromisoformat(path.stem)
        except ValueError:
            continue
        month_key = file_date.strftime("%Y-%m")
        if month_key >= current_month:
            continue  # don't touch the current month
        by_month[month_key].append(path)

    consolidated = 0
    for month_key, daily_files in sorted(by_month.items()):
        daily_files.sort(key=lambda p: p.stem)
        monthly_path = archive_dir / f"{month_key}.md"

        try:
            sections: list[str] = []
            for daily_path in daily_files:
                content = daily_path.read_text(encoding="utf-8", errors="replace").strip()
                sections.append(f"## {daily_path.stem}\n\n{content}")

            combined_body = "\n\n---\n\n".join(sections)
            post = frontmatter.Post(
                combined_body,
                **{"month": month_key, "days": len(daily_files)},
            )

            if monthly_path.exists():
                # Append to existing monthly file (in case consolidation was partial)
                existing = monthly_path.read_text(encoding="utf-8")
                monthly_path.write_text(existing + "\n\n---\n\n" + combined_body, encoding="utf-8")
            else:
                monthly_path.write_text(frontmatter.dumps(post), encoding="utf-8")

            # Delete daily files only after successful write
            for daily_path in daily_files:
                daily_path.unlink()
                log.debug(
                    "Housekeeping: consolidated %s into %s",
                    daily_path.name,
                    monthly_path.name,
                )

            consolidated += 1
            log.info(
                "Housekeeping: consolidated %d daily archive files into %s",
                len(daily_files),
                monthly_path.name,
            )

        except Exception:
            log.exception("Housekeeping: failed to consolidate month %s", month_key)

    return consolidated
