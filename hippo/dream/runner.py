"""Dream cycle orchestrator — runs the consolidation sub-agent."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import frontmatter
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)

from hippo.dream.prompts import DREAM_SYSTEM_PROMPT
from hippo.memory.server import create_dream_server

if TYPE_CHECKING:
    from hippo.config import HippoConfig
    from hippo.memory.buffer import ObsidianBufferStore
    from hippo.memory.mailbox import ObsidianMailboxStore
    from hippo.memory.types import BufferEntry, MailboxMessage

log = logging.getLogger(__name__)

# Guard against concurrent dream runs
_dream_running = asyncio.Event()


def _format_buffer_entries(entries: tuple[BufferEntry, ...]) -> str:
    if not entries:
        return ""
    lines = ["## Short-Term Buffer Entries\n"]
    for i, entry in enumerate(entries, 1):
        tags = ", ".join(entry.tags) if entry.tags else "none"
        lines.append(
            f"### Entry {i} [{entry.ts}] session={entry.session} tags=[{tags}]\n{entry.content}\n"
        )
    return "\n".join(lines)


def _format_inbox_messages(messages: tuple[MailboxMessage, ...]) -> str:
    if not messages:
        return ""
    lines = ["## Inbox Messages\n"]
    for i, msg in enumerate(messages, 1):
        lines.append(
            f"### Message {i} from={msg.from_bot} [{msg.ts}]\n"
            f"Subject: {msg.subject}\n\n"
            f"{msg.content}\n"
        )
    return "\n".join(lines)


def _build_query(
    buffer_entries: tuple[BufferEntry, ...], inbox_messages: tuple[MailboxMessage, ...]
) -> str:
    parts = [
        "Please consolidate the following entries into long-term memory.\n"
        "Follow your system prompt instructions exactly.\n"
    ]
    buffer_text = _format_buffer_entries(buffer_entries)
    inbox_text = _format_inbox_messages(inbox_messages)
    if buffer_text:
        parts.append(buffer_text)
    if inbox_text:
        parts.append(inbox_text)
    return "\n".join(parts)


async def _query_dream_agent(client: ClaudeSDKClient, query: str) -> str:
    """Send query to the dream sub-agent and collect the response."""
    await client.query(query)
    parts: list[str] = []
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
        elif isinstance(msg, ResultMessage):
            if msg.is_error:
                log.error("Dream agent error: %s", msg)
            break
    return "\n".join(parts) if parts else ""


def _write_dream_report(vault_path: Path, date: str, agent_output: str, is_empty: bool) -> str:
    """Write the dream report to ``dream_reports/YYYY-MM-DD.md``."""
    reports_dir = vault_path / "dream_reports"
    reports_dir.mkdir(exist_ok=True)

    body = "Nothing to consolidate — buffer and inbox were empty." if is_empty else agent_output

    post = frontmatter.Post(
        body,
        **{
            "date": date,
            "generated": datetime.now(UTC).isoformat(),
        },
    )
    report_path = reports_dir / f"{date}.md"
    report_path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return body


def _parse_summary_line(text: str, key: str) -> str:
    """Extract a value from the DREAM SUMMARY block by key."""
    pattern = rf"^{re.escape(key)}:\s*(.+)$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


async def run_dream(
    config: HippoConfig,
    buffer_store: ObsidianBufferStore,
    mailbox_store: ObsidianMailboxStore,
) -> str:
    """Run one full dream cycle.

    Returns the report text (also written to ``dream_reports/``).
    Returns immediately if another dream is already running.
    """
    if _dream_running.is_set():
        return "Dream cycle already in progress — try again later."

    _dream_running.set()
    date = datetime.now(UTC).strftime("%Y-%m-%d")

    try:
        buffer_entries = await buffer_store.read_buffer()
        inbox_messages = await mailbox_store.read_inbox()

        is_empty = not buffer_entries and not inbox_messages

        if is_empty:
            log.info("Dream cycle: buffer and inbox empty, skipping LLM")
            report = _write_dream_report(config.hippo_vault_path, date, "", is_empty=True)
            return report

        log.info(
            "Dream cycle: processing %d buffer entries, %d inbox messages",
            len(buffer_entries),
            len(inbox_messages),
        )

        dream_server = create_dream_server()
        options = ClaudeAgentOptions(
            system_prompt=DREAM_SYSTEM_PROMPT,
            mcp_servers={"memory": dream_server},
            permission_mode="bypassPermissions",
            model=config.hippo_dream_model,
            cwd=str(config.hippo_vault_path),
        )

        query = _build_query(buffer_entries, inbox_messages)
        agent_output = ""

        async with ClaudeSDKClient(options=options) as client:
            agent_output = await _query_dream_agent(client, query)

        report = _write_dream_report(config.hippo_vault_path, date, agent_output, is_empty=False)
        return report

    finally:
        # Always archive and clean up, even if the agent errored
        try:
            archived = await buffer_store.archive_buffer(date)
            log.info("Dream cycle: archived %d buffer entries", archived)
        except Exception:
            log.exception("Dream cycle: failed to archive buffer")

        try:
            cleared = await mailbox_store.clear_inbox()
            log.info("Dream cycle: cleared %d inbox messages", cleared)
        except Exception:
            log.exception("Dream cycle: failed to clear inbox")

        _dream_running.clear()
