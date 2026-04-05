"""Background scheduler — executes due tasks by querying the agent."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from aiogram import Bot
    from claude_agent_sdk import ClaudeSDKClient

    from hippo.config import HippoConfig
    from hippo.memory.buffer import ObsidianBufferStore
    from hippo.memory.mailbox import ObsidianMailboxStore
    from hippo.memory.scheduled import ObsidianScheduledStore
    from hippo.memory.types import ScheduledTask

log = logging.getLogger(__name__)

_DEFAULT_INTERVAL = 30.0


async def run_scheduler(
    config: HippoConfig,
    client: ClaudeSDKClient,
    client_lock: asyncio.Lock,
    bot: Bot,
    store: ObsidianScheduledStore,
    buffer_store: ObsidianBufferStore,
    mailbox_store: ObsidianMailboxStore,
    *,
    interval: float = _DEFAULT_INTERVAL,
) -> None:
    """Run the scheduler loop, checking for due tasks every `interval` seconds."""
    tz = ZoneInfo(config.hippo_timezone)
    log.info(
        "Scheduler started (interval=%.0fs, tz=%s, buffer_max=%d)",
        interval,
        config.hippo_timezone,
        config.hippo_buffer_max_entries,
    )
    while True:
        try:
            due_tasks = await store.get_due_tasks()
            for task in due_tasks:
                await _execute_task(
                    task, config, client, client_lock, bot, store, buffer_store, tz
                )
        except Exception:
            log.exception("Scheduler tick failed")

        try:
            await _maybe_trigger_dream(config, buffer_store, mailbox_store, bot)
        except Exception:
            log.exception("Buffer check failed")

        await asyncio.sleep(interval)


async def _maybe_trigger_dream(
    config: HippoConfig,
    buffer_store: ObsidianBufferStore,
    mailbox_store: ObsidianMailboxStore,
    bot: Bot,
) -> None:
    """Trigger the dream cycle automatically if the buffer is full."""
    from hippo.dream.runner import _dream_running, run_dream

    if _dream_running.is_set():
        return

    entries = await buffer_store.read_buffer()
    if len(entries) < config.hippo_buffer_max_entries:
        return

    log.info(
        "Buffer full (%d/%d entries) — triggering automatic dream cycle",
        len(entries),
        config.hippo_buffer_max_entries,
    )

    from hippo.telegram_bridge import convert_to_telegram

    report = await run_dream(config, buffer_store, mailbox_store)

    for user_id in config.allowed_telegram_ids:
        await bot.send_message(chat_id=user_id, text="💤 Dream cycle (auto)")
        for part in convert_to_telegram(report):
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=part["text"],  # type: ignore[arg-type]
                    entities=part["entities"],  # type: ignore[arg-type]
                )
            except Exception:
                try:
                    await bot.send_message(chat_id=user_id, text=str(part["text"]))
                except Exception:
                    log.exception("Failed to send dream report to %s", user_id)


async def _execute_task(
    task: ScheduledTask,
    config: HippoConfig,
    client: ClaudeSDKClient,
    client_lock: asyncio.Lock,
    bot: Bot,
    store: ObsidianScheduledStore,
    buffer_store: ObsidianBufferStore,
    tz: ZoneInfo,
) -> None:
    """Execute a single due task: query agent, send result, update state."""
    from hippo.memory.types import BufferEntry
    from hippo.telegram_bridge import convert_to_telegram, query_agent

    log.info("Executing task %s: %s", task.id, task.description)

    try:
        async with client_lock:
            response = await query_agent(client, task.description)
    except Exception:
        log.exception("Agent query failed for task %s", task.id)
        return

    # Feed result into the short-term buffer for dream consolidation
    entry = BufferEntry(
        ts=datetime.now(UTC).isoformat(),
        session=f"scheduler-{task.id}",
        content=f"Scheduled task [{task.description}]: {response}",
        tags=("scheduler",),
    )
    try:
        await buffer_store.append(entry)
    except Exception:
        log.exception("Failed to append scheduler result to buffer for task %s", task.id)

    # Send to all whitelisted users
    for user_id in config.allowed_telegram_ids:
        for part in convert_to_telegram(response):
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=part["text"],  # type: ignore[arg-type]
                    entities=part["entities"],  # type: ignore[arg-type]
                )
            except Exception:
                try:
                    await bot.send_message(chat_id=user_id, text=str(part["text"]))
                except Exception:
                    log.exception("Failed to send scheduled message to %s", user_id)

    # Update task state
    now = datetime.now(tz)
    if task.recurring:
        await store.update_last_run(task.id, now.isoformat())
        log.info("Recurring task %s: updated last_run", task.id)
    else:
        await store.mark_completed(task.id)
        log.info("One-shot task %s: marked completed", task.id)
