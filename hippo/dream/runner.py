"""Dream cycle orchestrator — runs the consolidation sub-agent."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

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
    from hippo.memory.episodic import ObsidianEpisodicStore
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


def _scan_raw_documents(vault_path: Path) -> list[tuple[str, str]]:
    """Scan ``raw/`` recursively for unprocessed documents.

    Returns a list of ``(relative_path, content)`` for ``.md``, ``.txt``,
    and ``.markdown`` files. Skips ``raw/processed/`` and its subtree.
    The relative path is relative to ``raw/`` (e.g. ``subdir/note.md``).
    """
    raw_dir = vault_path / "raw"
    if not raw_dir.is_dir():
        return []
    processed_dir = raw_dir / "processed"
    processed_dir.mkdir(exist_ok=True)
    documents: list[tuple[str, str]] = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue
        # Skip anything inside raw/processed/
        try:
            path.relative_to(processed_dir)
            continue  # it IS inside processed — skip
        except ValueError:
            pass
        if path.suffix.lower() not in {".md", ".txt", ".markdown"}:
            continue
        rel = str(path.relative_to(raw_dir))
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            log.warning("Raw ingest: could not read %s", rel)
            continue
        documents.append((rel, content))
    return documents


def _format_raw_documents(docs: list[tuple[str, str]]) -> str:
    if not docs:
        return ""
    _max_chars = 10_000
    lines = ["## Raw Documents for Ingest\n"]
    for i, (name, content) in enumerate(docs, 1):
        if len(content) > _max_chars:
            content = content[:_max_chars] + "\n[...truncated]"
        lines.append(f"### Document {i}: {name}\n{content}\n")
    return "\n".join(lines)


def _move_raw_to_processed(vault_path: Path, filenames: list[str]) -> int:
    """Move processed raw files to ``raw/processed/``. Returns count moved.

    ``filenames`` are relative paths from ``raw/`` (e.g. ``subdir/note.md``).
    The subdirectory structure is mirrored under ``raw/processed/``.
    """
    raw_dir = vault_path / "raw"
    processed_dir = raw_dir / "processed"
    processed_dir.mkdir(exist_ok=True)
    count = 0
    for rel in filenames:
        src = raw_dir / rel
        dst = processed_dir / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            count += 1
    return count


def _build_query(
    buffer_entries: tuple[BufferEntry, ...],
    inbox_messages: tuple[MailboxMessage, ...],
    raw_documents: list[tuple[str, str]] | None = None,
) -> str:
    parts = [
        "Please consolidate the following entries into long-term memory.\n"
        "Follow your system prompt instructions exactly.\n"
    ]
    buffer_text = _format_buffer_entries(buffer_entries)
    inbox_text = _format_inbox_messages(inbox_messages)
    raw_text = _format_raw_documents(raw_documents or [])
    if buffer_text:
        parts.append(buffer_text)
    if inbox_text:
        parts.append(inbox_text)
    if raw_text:
        parts.append(raw_text)
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


def _write_dream_report(vault_path: Path, date: str, body: str, *, is_empty: bool) -> str:
    """Write the dream report to ``dream_reports/YYYY-MM-DD.md``.

    First run of the day creates the file with YAML frontmatter.
    Subsequent runs on the same day append with a separator.
    Returns the body as written.
    """
    reports_dir = vault_path / "dream_reports"
    reports_dir.mkdir(exist_ok=True)

    run_ts = datetime.now(UTC).strftime("%H:%M UTC")
    report_path = reports_dir / f"{date}.md"

    if report_path.exists():
        existing = report_path.read_text(encoding="utf-8")
        report_path.write_text(
            existing + f"\n\n---\n\n## Run at {run_ts}\n\n{body}\n",
            encoding="utf-8",
        )
    else:
        post = frontmatter.Post(
            f"## Run at {run_ts}\n\n{body}",
            **{
                "date": date,
                "generated": datetime.now(UTC).isoformat(),
                "empty": is_empty,
            },
        )
        report_path.write_text(frontmatter.dumps(post), encoding="utf-8")

    return body


def _parse_summary_line(text: str, key: str) -> str:
    """Extract a value from the DREAM SUMMARY block by key."""
    pattern = rf"^{re.escape(key)}:\s*(.+)$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


async def _summarize_old_episodes(
    client: ClaudeSDKClient,
    episodic_store: ObsidianEpisodicStore,
    max_age_days: int,
) -> int:
    """Summarize old daily notes during the dream cycle.

    Returns the count of notes summarized.
    """
    try:
        candidates = await episodic_store.find_archivable_notes(max_age_days=max_age_days)
    except Exception:
        log.exception("Dream cycle: failed to find archivable notes")
        return 0

    if not candidates:
        return 0

    log.info("Dream cycle: summarizing %d old episodic notes", len(candidates))
    count = 0

    for date_str, path in candidates:
        try:
            original = path.read_text(encoding="utf-8", errors="replace")
            prompt = (
                f"Summarize the following daily note from {date_str} into a concise paragraph "
                f"(under 300 words). Preserve the most important events, decisions, and facts. "
                f"Output only the summary text, nothing else.\n\n---\n\n{original}"
            )
            summary = await _query_dream_agent(client, prompt)
            if summary:
                await episodic_store.archive_daily_note(date_str, summary.strip())
                count += 1
        except Exception:
            log.exception("Dream cycle: failed to summarize note %s", date_str)

    return count


async def run_dream(
    config: HippoConfig,
    buffer_store: ObsidianBufferStore,
    mailbox_store: ObsidianMailboxStore,
    episodic_store: ObsidianEpisodicStore | None = None,
) -> str:
    """Run one full dream cycle.

    Returns the report text (also written to ``dream_reports/``).
    Returns immediately if another dream is already running.
    """
    if _dream_running.is_set():
        return "Dream cycle already in progress — try again later."

    _dream_running.set()
    date = datetime.now(UTC).strftime("%Y-%m-%d")

    raw_docs: list[tuple[str, str]] = []
    agent_output = ""
    is_empty = True

    # Infrastructure stats — collected throughout and appended to the report.
    infra: dict[str, Any] = {
        "buffer_entries": 0,
        "inbox_messages": 0,
        "raw_docs": 0,
        "episodes_summarized": 0,
        "embeddings_rebuilt": False,
        "embeddings_entity_count": 0,
        "buffer_archived": 0,
        "inbox_cleared": 0,
        "raw_moved": 0,
        "_retention_days": config.hippo_retention_days,
    }

    try:
        buffer_entries = await buffer_store.read_buffer()
        inbox_messages = await mailbox_store.read_inbox()
        raw_docs = await asyncio.to_thread(_scan_raw_documents, config.hippo_vault_path)

        infra["buffer_entries"] = len(buffer_entries)
        infra["inbox_messages"] = len(inbox_messages)
        infra["raw_docs"] = len(raw_docs)

        is_empty = not buffer_entries and not inbox_messages and not raw_docs

        if is_empty:
            log.info("Dream cycle: buffer, inbox, and raw folder empty, skipping LLM")
        else:
            log.info(
                "Dream cycle: processing %d buffer entries, %d inbox messages, %d raw documents",
                len(buffer_entries),
                len(inbox_messages),
                len(raw_docs),
            )

            dream_server = create_dream_server()
            options = ClaudeAgentOptions(
                system_prompt=DREAM_SYSTEM_PROMPT,
                mcp_servers={"memory": dream_server},
                permission_mode="bypassPermissions",
                model=config.hippo_dream_model,
                cwd=str(config.hippo_vault_path),
            )

            query = _build_query(buffer_entries, inbox_messages, raw_docs)

            async with ClaudeSDKClient(options=options) as client:
                agent_output = await _query_dream_agent(client, query)
                if episodic_store is not None:
                    summarized = await _summarize_old_episodes(
                        client, episodic_store, config.hippo_episodic_archive_days
                    )
                    infra["episodes_summarized"] = summarized
                    if summarized:
                        log.info("Dream cycle: summarized %d old episodic notes", summarized)

            if config.hippo_embedding_model:
                try:
                    from hippo.memory.embeddings import rebuild_all_embeddings
                    from hippo.memory.semantic import _load_all

                    entities, _ = await asyncio.to_thread(_load_all, config.hippo_vault_path)
                    await asyncio.to_thread(
                        rebuild_all_embeddings,
                        config.hippo_vault_path,
                        entities,
                        config.hippo_embedding_model,
                    )
                    infra["embeddings_rebuilt"] = True
                    infra["embeddings_entity_count"] = len(entities)
                    log.info("Dream cycle: embedding index rebuilt (%d entities)", len(entities))
                except Exception:
                    log.exception("Dream cycle: failed to rebuild embeddings")

        try:
            from hippo.dream.housekeeping import run_housekeeping

            housekeeping_stats = await asyncio.to_thread(
                run_housekeeping, config.hippo_vault_path, config.hippo_retention_days
            )
            infra.update(housekeeping_stats)
            log.info("Dream cycle: housekeeping done — %s", housekeeping_stats)
        except Exception:
            log.exception("Dream cycle: housekeeping failed")

    finally:
        # Always archive and clean up, even if the agent errored.
        try:
            archived = await buffer_store.archive_buffer(date)
            infra["buffer_archived"] = archived
            log.info("Dream cycle: archived %d buffer entries", archived)
        except Exception:
            log.exception("Dream cycle: failed to archive buffer")

        try:
            cleared = await mailbox_store.clear_inbox()
            infra["inbox_cleared"] = cleared
            log.info("Dream cycle: cleared %d inbox messages", cleared)
        except Exception:
            log.exception("Dream cycle: failed to clear inbox")

        if raw_docs:
            try:
                moved = await asyncio.to_thread(
                    _move_raw_to_processed,
                    config.hippo_vault_path,
                    [name for name, _ in raw_docs],
                )
                infra["raw_moved"] = moved
                log.info("Dream cycle: moved %d raw documents to processed", moved)
            except Exception:
                log.exception("Dream cycle: failed to move raw documents")

        _dream_running.clear()

    # Build and write the report after all cleanup is done so infra stats are complete.
    full_content = _build_report_content(agent_output, is_empty, infra)
    report = _write_dream_report(config.hippo_vault_path, date, full_content, is_empty=is_empty)
    return report


def _build_report_content(
    agent_output: str,
    is_empty: bool,
    infra: dict[str, Any],
) -> str:
    """Combine agent output with a structured infrastructure section."""
    lines: list[str] = []

    if is_empty:
        lines.append("Nothing to consolidate — buffer and inbox were empty.")
    else:
        if agent_output:
            lines.append(agent_output)

    # Infrastructure section — always shown so the report is self-contained.
    lines.append("\n---\n\n## Infrastructure")

    ep_sum = int(infra.get("episodes_summarized", 0))
    emb_rebuilt = bool(infra.get("embeddings_rebuilt", False))
    emb_count = int(infra.get("embeddings_entity_count", 0))

    lines.append(
        f"- Input: {infra['buffer_entries']} buffer entries, "
        f"{infra['inbox_messages']} inbox messages, "
        f"{infra['raw_docs']} raw documents"
    )
    lines.append(f"- Buffer archived: {infra['buffer_archived']} entries")
    lines.append(f"- Inbox cleared: {infra['inbox_cleared']} messages")
    lines.append(f"- Raw documents moved to processed: {infra['raw_moved']}")
    lines.append(
        f"- Episodes summarized: {ep_sum}"
        + (" (old daily notes compressed and archived)" if ep_sum else "")
    )
    if emb_rebuilt:
        lines.append(
            f"- Embedding index rebuilt: {emb_count} entities indexed in semantic/embeddings.json"
        )
    else:
        lines.append("- Embedding index: not rebuilt (model not configured or rebuild failed)")

    # Housekeeping section — only shown if housekeeping ran.
    hk_keys = (
        "buffer_archives_pruned",
        "dream_reports_pruned",
        "completed_tasks_pruned",
        "raw_processed_pruned",
        "archive_months_consolidated",
    )
    if any(infra.get(k) for k in hk_keys):
        retention = int(infra.get("_retention_days", 0))
        days_suffix = f" (>{retention} days)" if retention else ""
        lines.append("\n## Housekeeping")
        pruned_labels = {
            "buffer_archives_pruned": "Buffer archives pruned",
            "dream_reports_pruned": "Dream reports pruned",
            "completed_tasks_pruned": "Completed tasks pruned",
            "raw_processed_pruned": "Raw processed files pruned",
        }
        for key, label in pruned_labels.items():
            val = int(infra.get(key, 0))
            if val:
                lines.append(f"- {label}: {val}{days_suffix}")
        consolidated = int(infra.get("archive_months_consolidated", 0))
        if consolidated:
            lines.append(f"- Episodic archive months consolidated: {consolidated}")
    else:
        lines.append("\n## Housekeeping\n- Nothing to clean up.")

    return "\n".join(lines)
