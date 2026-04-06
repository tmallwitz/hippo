"""Tests for hippo.dream.housekeeping."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import frontmatter

from hippo.dream.housekeeping import (
    _consolidate_episodic_archives,
    _prune_by_mtime,
    _prune_completed_tasks,
    _prune_dated_files,
    run_housekeeping,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dated_file(directory: Path, stem: str, content: str = "# content\n") -> Path:
    """Write a dated .md file (stem = YYYY-MM-DD)."""
    path = directory / f"{stem}.md"
    path.write_text(content, encoding="utf-8")
    return path


def _old_date(days: int = 100) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _recent_date(days: int = 10) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# _prune_dated_files
# ---------------------------------------------------------------------------


class TestPruneDatedFiles:
    def test_deletes_old_files(self, tmp_path: Path) -> None:
        d = tmp_path / "processed"
        d.mkdir()
        old = _dated_file(d, _old_date(100))
        cutoff = date.today() - timedelta(days=90)
        count = _prune_dated_files(d, "*.md", cutoff)
        assert count == 1
        assert not old.exists()

    def test_keeps_recent_files(self, tmp_path: Path) -> None:
        d = tmp_path / "processed"
        d.mkdir()
        recent = _dated_file(d, _recent_date(10))
        cutoff = date.today() - timedelta(days=90)
        count = _prune_dated_files(d, "*.md", cutoff)
        assert count == 0
        assert recent.exists()

    def test_skips_non_dated_files(self, tmp_path: Path) -> None:
        d = tmp_path / "processed"
        d.mkdir()
        non_dated = d / "README.md"
        non_dated.write_text("hi")
        cutoff = date.today() - timedelta(days=1)
        count = _prune_dated_files(d, "*.md", cutoff)
        assert count == 0
        assert non_dated.exists()

    def test_missing_directory_returns_zero(self, tmp_path: Path) -> None:
        count = _prune_dated_files(tmp_path / "nonexistent", "*.md", date.today())
        assert count == 0

    def test_boundary_same_day_kept(self, tmp_path: Path) -> None:
        d = tmp_path / "processed"
        d.mkdir()
        exactly_cutoff = date.today() - timedelta(days=90)
        f = _dated_file(d, exactly_cutoff.isoformat())
        cutoff = date.today() - timedelta(days=90)
        count = _prune_dated_files(d, "*.md", cutoff)
        # file_date == cutoff → NOT less than cutoff → kept
        assert count == 0
        assert f.exists()


# ---------------------------------------------------------------------------
# _prune_by_mtime
# ---------------------------------------------------------------------------


class TestPruneByMtime:
    def test_deletes_old_files_by_mtime(self, tmp_path: Path) -> None:
        d = tmp_path / "raw_processed"
        d.mkdir()
        old_file = d / "old.txt"
        old_file.write_text("old")
        # Backdate mtime to 100 days ago
        import os
        import time

        old_ts = time.time() - 100 * 86400
        os.utime(old_file, (old_ts, old_ts))

        cutoff = date.today() - timedelta(days=90)
        count = _prune_by_mtime(d, cutoff)
        assert count == 1
        assert not old_file.exists()

    def test_keeps_recent_files(self, tmp_path: Path) -> None:
        d = tmp_path / "raw_processed"
        d.mkdir()
        recent = d / "recent.txt"
        recent.write_text("new")
        cutoff = date.today() - timedelta(days=90)
        count = _prune_by_mtime(d, cutoff)
        assert count == 0
        assert recent.exists()

    def test_removes_empty_subdirectories(self, tmp_path: Path) -> None:
        import os
        import time

        d = tmp_path / "raw_processed"
        sub = d / "sub"
        sub.mkdir(parents=True)
        old_file = sub / "old.txt"
        old_file.write_text("old")
        old_ts = time.time() - 100 * 86400
        os.utime(old_file, (old_ts, old_ts))

        cutoff = date.today() - timedelta(days=90)
        _prune_by_mtime(d, cutoff)
        assert not sub.exists()


# ---------------------------------------------------------------------------
# _prune_completed_tasks
# ---------------------------------------------------------------------------


def _write_task(directory: Path, name: str, status: str, created: str) -> Path:
    path = directory / name
    post = frontmatter.Post("task body", status=status, created=created)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path


class TestPruneCompletedTasks:
    def test_deletes_old_completed_tasks(self, tmp_path: Path) -> None:
        d = tmp_path / "scheduled"
        d.mkdir()
        old_ts = (date.today() - timedelta(days=100)).isoformat() + "T00:00:00"
        task = _write_task(d, "task-abc123.md", "completed", old_ts)
        cutoff = date.today() - timedelta(days=90)
        count = _prune_completed_tasks(d, cutoff)
        assert count == 1
        assert not task.exists()

    def test_keeps_recent_completed_tasks(self, tmp_path: Path) -> None:
        d = tmp_path / "scheduled"
        d.mkdir()
        recent_ts = (date.today() - timedelta(days=10)).isoformat() + "T00:00:00"
        task = _write_task(d, "task-abc123.md", "completed", recent_ts)
        cutoff = date.today() - timedelta(days=90)
        count = _prune_completed_tasks(d, cutoff)
        assert count == 0
        assert task.exists()

    def test_keeps_pending_tasks_regardless_of_age(self, tmp_path: Path) -> None:
        d = tmp_path / "scheduled"
        d.mkdir()
        old_ts = (date.today() - timedelta(days=200)).isoformat() + "T00:00:00"
        pending = _write_task(d, "task-pending.md", "pending", old_ts)
        active = _write_task(d, "task-active.md", "active", old_ts)
        cutoff = date.today() - timedelta(days=90)
        count = _prune_completed_tasks(d, cutoff)
        assert count == 0
        assert pending.exists()
        assert active.exists()

    def test_missing_directory_returns_zero(self, tmp_path: Path) -> None:
        count = _prune_completed_tasks(tmp_path / "nonexistent", date.today())
        assert count == 0

    def test_skips_malformed_files(self, tmp_path: Path) -> None:
        d = tmp_path / "scheduled"
        d.mkdir()
        bad = d / "task-bad.md"
        bad.write_text("not valid frontmatter {{{{")
        cutoff = date.today() - timedelta(days=90)
        # Should not raise
        count = _prune_completed_tasks(d, cutoff)
        assert count == 0


# ---------------------------------------------------------------------------
# _consolidate_episodic_archives
# ---------------------------------------------------------------------------


class TestConsolidateEpisodicArchives:
    def _past_month(self, months_ago: int = 2) -> str:
        """Return a YYYY-MM string for a past month."""
        today = date.today()
        month = today.month - months_ago
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        return f"{year}-{month:02d}"

    def test_consolidates_daily_files_into_monthly(self, tmp_path: Path) -> None:
        archive = tmp_path / "episodic" / "archive"
        archive.mkdir(parents=True)
        month = self._past_month(2)

        for day in ("01", "02", "03"):
            f = archive / f"{month}-{day}.md"
            f.write_text(f"# Day {day}\n\nContent for day {day}.", encoding="utf-8")

        count = _consolidate_episodic_archives(archive)
        assert count == 1
        monthly = archive / f"{month}.md"
        assert monthly.exists()

        content = monthly.read_text(encoding="utf-8")
        assert "Day 01" in content
        assert "Day 02" in content
        assert "Day 03" in content

    def test_daily_files_deleted_after_consolidation(self, tmp_path: Path) -> None:
        archive = tmp_path / "episodic" / "archive"
        archive.mkdir(parents=True)
        month = self._past_month(2)

        daily_paths = []
        for day in ("10", "11"):
            f = archive / f"{month}-{day}.md"
            f.write_text(f"Content {day}")
            daily_paths.append(f)

        _consolidate_episodic_archives(archive)
        for p in daily_paths:
            assert not p.exists()

    def test_current_month_files_left_alone(self, tmp_path: Path) -> None:
        archive = tmp_path / "episodic" / "archive"
        archive.mkdir(parents=True)
        today = date.today()
        current_month = today.strftime("%Y-%m")

        f = archive / f"{current_month}-01.md"
        f.write_text("current month content")

        count = _consolidate_episodic_archives(archive)
        assert count == 0
        assert f.exists()

    def test_monthly_file_content_includes_separators(self, tmp_path: Path) -> None:
        archive = tmp_path / "episodic" / "archive"
        archive.mkdir(parents=True)
        month = self._past_month(2)

        (archive / f"{month}-05.md").write_text("Alpha")
        (archive / f"{month}-06.md").write_text("Beta")

        _consolidate_episodic_archives(archive)
        content = (archive / f"{month}.md").read_text(encoding="utf-8")
        assert "---" in content
        assert "Alpha" in content
        assert "Beta" in content

    def test_existing_monthly_file_gets_appended(self, tmp_path: Path) -> None:
        archive = tmp_path / "episodic" / "archive"
        archive.mkdir(parents=True)
        month = self._past_month(3)

        existing = archive / f"{month}.md"
        existing.write_text("existing content\n")

        (archive / f"{month}-15.md").write_text("New day")

        _consolidate_episodic_archives(archive)
        content = existing.read_text(encoding="utf-8")
        assert "existing content" in content
        assert "New day" in content

    def test_already_consolidated_monthly_files_skipped(self, tmp_path: Path) -> None:
        archive = tmp_path / "episodic" / "archive"
        archive.mkdir(parents=True)
        month = self._past_month(2)

        monthly = archive / f"{month}.md"
        monthly.write_text("already consolidated")

        count = _consolidate_episodic_archives(archive)
        assert count == 0  # no daily files to consolidate
        assert monthly.read_text(encoding="utf-8") == "already consolidated"

    def test_missing_directory_returns_zero(self, tmp_path: Path) -> None:
        count = _consolidate_episodic_archives(tmp_path / "nonexistent")
        assert count == 0


# ---------------------------------------------------------------------------
# run_housekeeping (integration)
# ---------------------------------------------------------------------------


class TestRunHousekeeping:
    def test_returns_stats_dict(self, tmp_path: Path) -> None:
        stats = run_housekeeping(tmp_path, retention_days=90)
        assert set(stats.keys()) == {
            "buffer_archives_pruned",
            "dream_reports_pruned",
            "completed_tasks_pruned",
            "raw_processed_pruned",
            "archive_months_consolidated",
        }

    def test_prunes_across_all_directories(self, tmp_path: Path) -> None:
        retention = 90
        cutoff_days = retention + 10  # clearly older than cutoff

        # buffer archives
        buf_dir = tmp_path / "short_term" / "processed"
        buf_dir.mkdir(parents=True)
        _dated_file(buf_dir, _old_date(cutoff_days))

        # dream reports
        rep_dir = tmp_path / "dream_reports"
        rep_dir.mkdir()
        _dated_file(rep_dir, _old_date(cutoff_days))

        # completed task
        sched_dir = tmp_path / "scheduled"
        sched_dir.mkdir()
        old_ts = (date.today() - timedelta(days=cutoff_days)).isoformat() + "T12:00:00"
        _write_task(sched_dir, "task-xyz.md", "completed", old_ts)

        stats = run_housekeeping(tmp_path, retention_days=retention)
        assert stats["buffer_archives_pruned"] == 1
        assert stats["dream_reports_pruned"] == 1
        assert stats["completed_tasks_pruned"] == 1

    def test_empty_vault_returns_zeros(self, tmp_path: Path) -> None:
        stats = run_housekeeping(tmp_path, retention_days=90)
        assert all(v == 0 for v in stats.values())
