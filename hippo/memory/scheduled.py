"""Obsidian-vault-backed scheduled task store (one Markdown file per task)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import frontmatter
from croniter import croniter

from hippo.memory.types import ScheduledTask

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _task_path(vault_path: Path, task_id: str) -> Path:
    return vault_path / "scheduled" / f"task-{task_id}.md"


def _generate_id() -> str:
    return uuid.uuid4().hex[:8]


def _parse_task_file(path: Path) -> ScheduledTask:
    """Parse a task Markdown file into a ScheduledTask."""
    post = frontmatter.load(str(path))
    meta = post.metadata
    return ScheduledTask(
        id=str(meta["id"]),
        description=str(meta["description"]),
        time=str(meta["time"]) if meta.get("time") else None,
        recurring=bool(meta.get("recurring", False)),
        cron=str(meta["cron"]) if meta.get("cron") else None,
        status=str(meta.get("status", "pending")),
        created=str(meta["created"]),
        last_run=str(meta["last_run"]) if meta.get("last_run") else None,
    )


def _write_task_file(path: Path, task: ScheduledTask) -> None:
    """Write a ScheduledTask to a frontmatter-only Markdown file."""
    meta = {
        "id": task.id,
        "description": task.description,
        "time": task.time,
        "recurring": task.recurring,
        "cron": task.cron,
        "status": task.status,
        "created": task.created,
        "last_run": task.last_run,
    }
    post = frontmatter.Post("", **meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")


def _is_due_oneshot(task: ScheduledTask, now: datetime) -> bool:
    """Check if a one-shot task is due."""
    if task.status != "pending" or task.time is None:
        return False
    task_time = datetime.fromisoformat(task.time)
    # Make naive datetimes comparable
    if task_time.tzinfo is None and now.tzinfo is not None:
        task_time = task_time.replace(tzinfo=now.tzinfo)
    return task_time <= now


def _is_due_cron(task: ScheduledTask, now: datetime) -> bool:
    """Check if a recurring cron task is due since its last run."""
    if task.status != "active" or task.cron is None:
        return False
    # Determine the reference point (last_run or created)
    ref_str = task.last_run or task.created
    ref_time = datetime.fromisoformat(ref_str)
    if ref_time.tzinfo is None and now.tzinfo is not None:
        ref_time = ref_time.replace(tzinfo=now.tzinfo)

    # Get the most recent firing time before now
    cron = croniter(task.cron, now)
    prev_fire: datetime = cron.get_prev(datetime)
    return bool(prev_fire > ref_time)


# ---------------------------------------------------------------------------
# Public store class
# ---------------------------------------------------------------------------


class ObsidianScheduledStore:
    """Scheduled task store backed by Markdown files in the vault."""

    def __init__(self, vault_path: Path, timezone: str) -> None:
        self._vault = vault_path
        self._tz = ZoneInfo(timezone)
        self._lock = asyncio.Lock()
        (vault_path / "scheduled").mkdir(parents=True, exist_ok=True)

    # -- Create ---------------------------------------------------------------

    async def create_task(
        self,
        description: str,
        time: str | None = None,
        cron_expr: str | None = None,
    ) -> ScheduledTask:
        async with self._lock:
            return await asyncio.to_thread(self._create_task_sync, description, time, cron_expr)

    def _create_task_sync(
        self,
        description: str,
        time: str | None,
        cron_expr: str | None,
    ) -> ScheduledTask:
        if not time and not cron_expr:
            msg = "Must provide either 'time' (ISO datetime) or 'cron' expression"
            raise ValueError(msg)
        if time and cron_expr:
            msg = "Provide either 'time' or 'cron', not both"
            raise ValueError(msg)

        if cron_expr and not croniter.is_valid(cron_expr):
            msg = f"Invalid cron expression: {cron_expr}"
            raise ValueError(msg)

        now = datetime.now(self._tz)
        task_id = _generate_id()
        recurring = cron_expr is not None

        task = ScheduledTask(
            id=task_id,
            description=description,
            time=time,
            recurring=recurring,
            cron=cron_expr,
            status="active" if recurring else "pending",
            created=now.isoformat(),
        )
        path = _task_path(self._vault, task_id)
        _write_task_file(path, task)
        return task

    # -- List -----------------------------------------------------------------

    async def list_tasks(self) -> list[ScheduledTask]:
        return await asyncio.to_thread(self._list_tasks_sync)

    def _list_tasks_sync(self) -> list[ScheduledTask]:
        scheduled_dir = self._vault / "scheduled"
        if not scheduled_dir.is_dir():
            return []
        tasks: list[ScheduledTask] = []
        for path in scheduled_dir.glob("task-*.md"):
            try:
                task = _parse_task_file(path)
                if task.status in ("pending", "active"):
                    tasks.append(task)
            except Exception:
                log.warning("Skipping unparseable task file: %s", path)
        return tasks

    # -- Cancel ---------------------------------------------------------------

    async def cancel_task(self, task_id: str) -> bool:
        async with self._lock:
            return await asyncio.to_thread(self._cancel_task_sync, task_id)

    def _cancel_task_sync(self, task_id: str) -> bool:
        path = _task_path(self._vault, task_id)
        if path.exists():
            path.unlink()
            return True
        return False

    # -- Due detection --------------------------------------------------------

    async def get_due_tasks(self) -> list[ScheduledTask]:
        return await asyncio.to_thread(self._get_due_tasks_sync)

    def _get_due_tasks_sync(self) -> list[ScheduledTask]:
        now = datetime.now(self._tz)
        scheduled_dir = self._vault / "scheduled"
        if not scheduled_dir.is_dir():
            return []
        due: list[ScheduledTask] = []
        for path in scheduled_dir.glob("task-*.md"):
            try:
                task = _parse_task_file(path)
                if _is_due_oneshot(task, now) or _is_due_cron(task, now):
                    due.append(task)
            except Exception:
                log.warning("Skipping unparseable task file: %s", path)
        return due

    # -- State updates --------------------------------------------------------

    async def mark_completed(self, task_id: str) -> None:
        async with self._lock:
            await asyncio.to_thread(self._mark_completed_sync, task_id)

    def _mark_completed_sync(self, task_id: str) -> None:
        path = _task_path(self._vault, task_id)
        if not path.exists():
            return
        task = _parse_task_file(path)
        updated = ScheduledTask(
            id=task.id,
            description=task.description,
            time=task.time,
            recurring=task.recurring,
            cron=task.cron,
            status="completed",
            created=task.created,
            last_run=task.last_run,
        )
        _write_task_file(path, updated)

    async def update_last_run(self, task_id: str, run_time: str) -> None:
        async with self._lock:
            await asyncio.to_thread(self._update_last_run_sync, task_id, run_time)

    def _update_last_run_sync(self, task_id: str, run_time: str) -> None:
        path = _task_path(self._vault, task_id)
        if not path.exists():
            return
        task = _parse_task_file(path)
        updated = ScheduledTask(
            id=task.id,
            description=task.description,
            time=task.time,
            recurring=task.recurring,
            cron=task.cron,
            status=task.status,
            created=task.created,
            last_run=run_time,
        )
        _write_task_file(path, updated)
