"""Tests for ObsidianScheduledStore."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import frontmatter
import pytest

from hippo.memory.scheduled import ObsidianScheduledStore

TZ = "UTC"
_tz = ZoneInfo(TZ)


@pytest.fixture()
def store(tmp_vault: Path) -> ObsidianScheduledStore:
    return ObsidianScheduledStore(tmp_vault, TZ)


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------


class TestCreateTask:
    async def test_create_oneshot(self, store: ObsidianScheduledStore) -> None:
        task = await store.create_task("Drink water", time="2026-04-06T10:00")
        assert task.description == "Drink water"
        assert task.time == "2026-04-06T10:00"
        assert task.recurring is False
        assert task.status == "pending"
        assert task.cron is None

    async def test_create_recurring(self, store: ObsidianScheduledStore) -> None:
        task = await store.create_task("Weekly review", cron_expr="0 17 * * 5")
        assert task.description == "Weekly review"
        assert task.recurring is True
        assert task.status == "active"
        assert task.cron == "0 17 * * 5"
        assert task.time is None

    async def test_must_provide_time_or_cron(self, store: ObsidianScheduledStore) -> None:
        with pytest.raises(ValueError, match="Must provide"):
            await store.create_task("No time")

    async def test_must_not_provide_both(self, store: ObsidianScheduledStore) -> None:
        with pytest.raises(ValueError, match="not both"):
            await store.create_task("Both", time="2026-04-06T10:00", cron_expr="* * * * *")

    async def test_invalid_cron(self, store: ObsidianScheduledStore) -> None:
        with pytest.raises(ValueError, match="Invalid cron"):
            await store.create_task("Bad cron", cron_expr="not a cron")

    async def test_file_created(self, store: ObsidianScheduledStore, tmp_vault: Path) -> None:
        task = await store.create_task("Test", time="2026-04-06T10:00")
        path = tmp_vault / "scheduled" / f"task-{task.id}.md"
        assert path.exists()

    async def test_file_frontmatter(self, store: ObsidianScheduledStore, tmp_vault: Path) -> None:
        task = await store.create_task("Test task", time="2026-04-06T10:00")
        path = tmp_vault / "scheduled" / f"task-{task.id}.md"
        post = frontmatter.load(str(path))
        assert post.metadata["description"] == "Test task"
        assert post.metadata["status"] == "pending"

    async def test_unique_ids(self, store: ObsidianScheduledStore) -> None:
        t1 = await store.create_task("A", time="2026-04-06T10:00")
        t2 = await store.create_task("B", time="2026-04-06T11:00")
        assert t1.id != t2.id


# ---------------------------------------------------------------------------
# list_tasks
# ---------------------------------------------------------------------------


class TestListTasks:
    async def test_list_empty(self, store: ObsidianScheduledStore) -> None:
        tasks = await store.list_tasks()
        assert tasks == []

    async def test_list_pending_and_active(self, store: ObsidianScheduledStore) -> None:
        await store.create_task("One-shot", time="2026-04-06T10:00")
        await store.create_task("Recurring", cron_expr="0 9 * * *")
        tasks = await store.list_tasks()
        assert len(tasks) == 2
        statuses = {t.status for t in tasks}
        assert statuses == {"pending", "active"}

    async def test_excludes_completed(self, store: ObsidianScheduledStore) -> None:
        task = await store.create_task("Done soon", time="2026-04-06T10:00")
        await store.mark_completed(task.id)
        tasks = await store.list_tasks()
        assert len(tasks) == 0


# ---------------------------------------------------------------------------
# cancel_task
# ---------------------------------------------------------------------------


class TestCancelTask:
    async def test_cancel_existing(self, store: ObsidianScheduledStore, tmp_vault: Path) -> None:
        task = await store.create_task("Cancel me", time="2026-04-06T10:00")
        result = await store.cancel_task(task.id)
        assert result is True
        assert not (tmp_vault / "scheduled" / f"task-{task.id}.md").exists()

    async def test_cancel_nonexistent(self, store: ObsidianScheduledStore) -> None:
        result = await store.cancel_task("nonexistent")
        assert result is False


# ---------------------------------------------------------------------------
# get_due_tasks
# ---------------------------------------------------------------------------


class TestGetDueTasks:
    async def test_oneshot_due(self, store: ObsidianScheduledStore) -> None:
        past = (datetime.now(_tz) - timedelta(minutes=5)).isoformat()
        await store.create_task("Overdue", time=past)
        due = await store.get_due_tasks()
        assert len(due) == 1
        assert due[0].description == "Overdue"

    async def test_oneshot_not_due(self, store: ObsidianScheduledStore) -> None:
        future = (datetime.now(_tz) + timedelta(hours=1)).isoformat()
        await store.create_task("Future", time=future)
        due = await store.get_due_tasks()
        assert len(due) == 0

    async def test_completed_skipped(self, store: ObsidianScheduledStore) -> None:
        past = (datetime.now(_tz) - timedelta(minutes=5)).isoformat()
        task = await store.create_task("Done", time=past)
        await store.mark_completed(task.id)
        due = await store.get_due_tasks()
        assert len(due) == 0

    async def test_recurring_due(self, store: ObsidianScheduledStore) -> None:
        # Create a recurring task with cron "every minute" and last_run 2 minutes ago
        task = await store.create_task("Every minute", cron_expr="* * * * *")
        two_min_ago = (datetime.now(_tz) - timedelta(minutes=2)).isoformat()
        await store.update_last_run(task.id, two_min_ago)
        due = await store.get_due_tasks()
        assert len(due) == 1

    async def test_recurring_not_due(self, store: ObsidianScheduledStore) -> None:
        # Create with cron "yearly" — won't be due
        task = await store.create_task("Yearly", cron_expr="0 0 1 1 *")
        # Set last_run to just now
        await store.update_last_run(task.id, datetime.now(_tz).isoformat())
        due = await store.get_due_tasks()
        assert len(due) == 0


# ---------------------------------------------------------------------------
# State updates
# ---------------------------------------------------------------------------


class TestStateUpdates:
    async def test_mark_completed(self, store: ObsidianScheduledStore, tmp_vault: Path) -> None:
        task = await store.create_task("Complete me", time="2026-04-06T10:00")
        await store.mark_completed(task.id)
        path = tmp_vault / "scheduled" / f"task-{task.id}.md"
        post = frontmatter.load(str(path))
        assert post.metadata["status"] == "completed"

    async def test_update_last_run(self, store: ObsidianScheduledStore, tmp_vault: Path) -> None:
        task = await store.create_task("Recurring", cron_expr="0 9 * * *")
        now = datetime.now(_tz).isoformat()
        await store.update_last_run(task.id, now)
        path = tmp_vault / "scheduled" / f"task-{task.id}.md"
        post = frontmatter.load(str(path))
        assert str(post.metadata["last_run"]) == now


# ---------------------------------------------------------------------------
# Manual edits
# ---------------------------------------------------------------------------


class TestManualEdits:
    async def test_manually_created_task(
        self, store: ObsidianScheduledStore, tmp_vault: Path
    ) -> None:
        """A task file created by hand in Obsidian should be parseable."""
        path = tmp_vault / "scheduled" / "task-manual01.md"
        path.write_text(
            "---\n"
            "id: manual01\n"
            "description: Hand-written task\n"
            'time: "2026-04-06T10:00"\n'
            "recurring: false\n"
            "cron: null\n"
            "status: pending\n"
            'created: "2026-04-05T14:00"\n'
            "last_run: null\n"
            "---\n",
            encoding="utf-8",
        )
        tasks = await store.list_tasks()
        assert any(t.id == "manual01" for t in tasks)

    async def test_manually_edited_status(
        self, store: ObsidianScheduledStore, tmp_vault: Path
    ) -> None:
        task = await store.create_task("Edit me", time="2026-04-06T10:00")
        path = tmp_vault / "scheduled" / f"task-{task.id}.md"

        # Manually change status to completed
        text = path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: completed")
        path.write_text(text, encoding="utf-8")

        tasks = await store.list_tasks()
        assert not any(t.id == task.id for t in tasks)
