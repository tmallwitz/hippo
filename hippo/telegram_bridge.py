"""Telegram bot bridge — connects aiogram to the Claude Agent SDK client."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message, MessageEntity
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock
from telegramify_markdown import convert
from telegramify_markdown.config import get_runtime_config

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeSDKClient

    from hippo.config import HippoConfig
    from hippo.memory.buffer import ObsidianBufferStore
    from hippo.memory.episodic import ObsidianEpisodicStore
    from hippo.memory.mailbox import ObsidianMailboxStore
    from hippo.memory.scheduled import ObsidianScheduledStore
    from hippo.memory.semantic import ObsidianSemanticStore

log = logging.getLogger(__name__)

_TELEGRAM_MSG_LIMIT = 4096

# Configure telegramify-markdown for Claude-style output
_tg_cfg = get_runtime_config()
_tg_cfg.cite_expandable = True

_HELP_TEXT = """\
**Hippo commands**

/help — Show this message
/status — Buffer stats, last dream, next scheduled task
/tasks — List all pending and active scheduled tasks
/memory — Show recent entities and episodes (usage: /memory 5)
/dream — Trigger a dream consolidation cycle

I also understand voice messages and images.
"""


# ---------------------------------------------------------------------------
# Whitelist filter
# ---------------------------------------------------------------------------


class _WhitelistFilter(BaseFilter):
    """Only allow messages from whitelisted Telegram user IDs."""

    def __init__(self, allowed_ids: set[int]) -> None:
        self._allowed = allowed_ids

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        return message.from_user.id in self._allowed


# ---------------------------------------------------------------------------
# Markdown → Telegram conversion (public — also used by scheduler)
# ---------------------------------------------------------------------------


def _to_aiogram_entities(tg_entities: list[object]) -> list[MessageEntity]:
    """Convert telegramify-markdown entities to aiogram MessageEntity objects."""
    result: list[MessageEntity] = []
    for e in tg_entities:
        d = e.to_dict()  # type: ignore[attr-defined]
        result.append(MessageEntity(**d))
    return result


def convert_to_telegram(markdown_text: str) -> list[dict[str, object]]:
    """Convert Claude's Markdown into Telegram-ready (text, entities) chunks.

    Returns a list of dicts with 'text' and 'entities' keys, each fitting
    within Telegram's message length limit. Falls back to plain text on error.
    """
    try:
        text, entities = convert(markdown_text)
    except Exception:
        log.debug("telegramify-markdown conversion failed, sending as plain text")
        return [{"text": chunk, "entities": None} for chunk in _split_text(markdown_text)]

    if len(text) <= _TELEGRAM_MSG_LIMIT:
        return [{"text": text, "entities": _to_aiogram_entities(entities)}]

    # Long message: split at paragraph boundaries, re-convert each chunk
    chunks = _split_text(markdown_text)
    result: list[dict[str, object]] = []
    for chunk in chunks:
        try:
            t, ents = convert(chunk)
            result.append({"text": t, "entities": _to_aiogram_entities(ents)})
        except Exception:
            result.append({"text": chunk, "entities": None})
    return result


def _split_text(text: str) -> list[str]:
    """Split text into chunks that fit Telegram's message limit."""
    if len(text) <= _TELEGRAM_MSG_LIMIT:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= _TELEGRAM_MSG_LIMIT:
            chunks.append(text)
            break

        cut = text.rfind("\n\n", 0, _TELEGRAM_MSG_LIMIT)
        if cut == -1:
            cut = text.rfind(". ", 0, _TELEGRAM_MSG_LIMIT)
            if cut != -1:
                cut += 1
        if cut == -1:
            cut = _TELEGRAM_MSG_LIMIT

        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()

    return chunks


# ---------------------------------------------------------------------------
# Typing indicator
# ---------------------------------------------------------------------------


async def _keep_typing(bot: Bot, chat_id: int, stop: asyncio.Event) -> None:
    """Send typing action every 4 seconds until stopped."""
    while not stop.is_set():
        with contextlib.suppress(Exception):
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=4.0)


# ---------------------------------------------------------------------------
# Agent query helpers (public — also used by scheduler)
# ---------------------------------------------------------------------------


async def query_agent(client: ClaudeSDKClient, text: str) -> str:
    """Send a message to the agent and collect the text response."""
    await client.query(text)
    parts: list[str] = []
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
        elif isinstance(msg, ResultMessage):
            if msg.is_error:
                log.error("Agent error: %s", msg)
            break
    return "\n".join(parts) if parts else "(no response)"


async def query_agent_with_image(
    client: ClaudeSDKClient,
    image_b64: str,
    media_type: str,
    caption: str,
) -> str:
    """Send an image + text to the agent and collect the text response."""

    async def _image_message() -> AsyncIterator[dict[str, object]]:
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": caption},
                ],
            },
            "parent_tool_use_id": None,
            "session_id": "default",
        }

    await client.query(_image_message())
    parts: list[str] = []
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
        elif isinstance(msg, ResultMessage):
            if msg.is_error:
                log.error("Agent error: %s", msg)
            break
    return "\n".join(parts) if parts else "(no response)"


# ---------------------------------------------------------------------------
# Helpers for direct-read commands
# ---------------------------------------------------------------------------


async def _send_parts(message: Message, text: str) -> None:
    for part in convert_to_telegram(text):
        try:
            await message.answer(
                text=part["text"],  # type: ignore[arg-type]
                entities=part["entities"],  # type: ignore[arg-type]
            )
        except Exception:
            await message.answer(str(part["text"]))


def _last_dream_date(vault_path: object) -> str:
    from pathlib import Path

    reports_dir = Path(str(vault_path)) / "dream_reports"
    if not reports_dir.is_dir():
        return "never"
    files = sorted(reports_dir.glob("*.md"), reverse=True)
    if not files:
        return "never"
    return files[0].stem  # YYYY-MM-DD


def _count_raw_files(vault_path: object) -> int:
    """Count unprocessed files in ``raw/`` (excluding ``raw/processed/``)."""
    from pathlib import Path

    raw_dir = Path(str(vault_path)) / "raw"
    if not raw_dir.is_dir():
        return 0
    processed_dir = raw_dir / "processed"
    count = 0
    for path in raw_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            path.relative_to(processed_dir)
            continue  # inside processed/ — skip
        except ValueError:
            pass
        if path.suffix.lower() in {".md", ".txt", ".markdown"}:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------


async def run_bot(
    config: HippoConfig,
    client: ClaudeSDKClient,
    bot: Bot,
    client_lock: asyncio.Lock,
    buffer_store: ObsidianBufferStore,
    mailbox_store: ObsidianMailboxStore,
    scheduled_store: ObsidianScheduledStore,
    semantic_store: ObsidianSemanticStore,
    episodic_store: ObsidianEpisodicStore,
) -> None:
    """Start the Telegram bot and poll for messages."""
    from hippo.dream.runner import run_dream
    from hippo.memory.types import BufferEntry

    dp = Dispatcher()

    allowed_ids = set(config.allowed_telegram_ids)
    whitelist = _WhitelistFilter(allowed_ids)

    # ------------------------------------------------------------------ /help
    @dp.message(whitelist, Command("help"))
    async def handle_help(message: Message) -> None:
        await _send_parts(message, _HELP_TEXT)

    # ----------------------------------------------------------------- /dream
    @dp.message(whitelist, Command("dream"))
    async def handle_dream(message: Message) -> None:
        chat_id = message.chat.id
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await message.answer("Dreaming… this may take a moment.")

        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing(bot, chat_id, stop_typing))
        try:
            report = await run_dream(config, buffer_store, mailbox_store, episodic_store)
        except Exception as exc:
            log.exception("Dream cycle failed")
            report = f"Dream cycle failed: {exc}"
        finally:
            stop_typing.set()
            await typing_task

        await _send_parts(message, report)

    # ---------------------------------------------------------------- /status
    @dp.message(whitelist, Command("status"))
    async def handle_status(message: Message) -> None:
        entries = await buffer_store.read_buffer()
        entry_count = len(entries)
        max_entries = config.hippo_buffer_max_entries
        last_dream = _last_dream_date(config.hippo_vault_path)

        inbox_messages = await mailbox_store.read_inbox()
        inbox_count = len(inbox_messages)

        raw_count = await asyncio.to_thread(_count_raw_files, config.hippo_vault_path)

        tasks = await scheduled_store.list_tasks()
        pending = [t for t in tasks if t.status in ("pending", "active")]
        if pending:
            # Sort one-shot tasks by time, put recurring last
            one_shot = sorted([t for t in pending if t.time], key=lambda t: t.time or "")
            recurring = [t for t in pending if t.recurring]
            if one_shot:
                next_task = one_shot[0].description
            else:
                next_task = f"{recurring[0].description} (recurring)"
        else:
            next_task = "none"

        lines = [
            "**Status**",
            f"Buffer: {entry_count}/{max_entries} entries",
            f"Inbox: {inbox_count} message{'s' if inbox_count != 1 else ''} waiting",
            f"Raw: {raw_count} file{'s' if raw_count != 1 else ''} waiting for ingest",
            f"Last dream: {last_dream}",
            f"Next task: {next_task}",
        ]
        await _send_parts(message, "\n".join(lines))

    # ---------------------------------------------------------------- /tasks
    @dp.message(whitelist, Command("tasks"))
    async def handle_tasks(message: Message) -> None:
        tasks = await scheduled_store.list_tasks()
        if not tasks:
            await message.answer("No pending or active scheduled tasks.")
            return

        lines = ["**Scheduled tasks**"]
        for t in tasks:
            schedule = t.cron if t.recurring else (t.time or "?")
            lines.append(f"`[{t.id}]` {t.status} — {schedule}\n  {t.description}")

        await _send_parts(message, "\n\n".join(lines))

    # --------------------------------------------------------------- /memory
    @dp.message(whitelist, Command("memory"))
    async def handle_memory(message: Message) -> None:
        n = 5
        if message.text:
            parts = message.text.split()
            if len(parts) >= 2:
                with contextlib.suppress(ValueError):
                    n = max(1, min(50, int(parts[1])))

        graph = await semantic_store.read_graph()
        entities = list(graph.entities[-n:])

        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        episodes = await episodic_store.recall_episodes(end_date=today_str)
        recent_episodes = episodes[-n:]

        lines = [f"**Memory (last {n})**", "", "**Entities:**"]
        if entities:
            for e in entities:
                obs_preview = f" — {e.observations[0]}" if e.observations else ""
                lines.append(f"• **{e.name}** ({e.entity_type}){obs_preview}")
        else:
            lines.append("No entities yet.")

        lines.append("")
        lines.append("**Episodes:**")
        if recent_episodes:
            for ep in recent_episodes:
                lines.append(f"• {ep.date} {ep.time} — {ep.title}")
        else:
            lines.append("No episodes yet.")

        await _send_parts(message, "\n".join(lines))

    # ------------------------------------------------------------ Voice messages
    @dp.message(whitelist, F.voice)
    async def handle_voice(message: Message) -> None:
        from hippo import voice as voice_mod

        chat_id = message.chat.id
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing(bot, chat_id, stop_typing))

        try:
            file = await bot.get_file(message.voice.file_id)  # type: ignore[union-attr]
            bio = await bot.download_file(file.file_path)  # type: ignore[arg-type]
            audio_bytes = bio.read()  # type: ignore[union-attr]

            transcript = await voice_mod.transcribe(
                audio_bytes, config.hippo_whisper_model, config.hippo_whisper_language
            )
        finally:
            stop_typing.set()
            await typing_task

        if not transcript:
            await message.answer("I could not understand the voice message.")
            return

        await message.answer(f"_Transcript:_ {transcript}", parse_mode="Markdown")

        user_id = message.from_user.id if message.from_user else 0
        now = datetime.now(UTC).isoformat(timespec="seconds")
        entry = BufferEntry(
            ts=now,
            session=f"tg-voice-{user_id}",
            content=f"[Voice transcript] {transcript}",
            tags=("voice",),
        )
        await buffer_store.append(entry)

        stop_typing2 = asyncio.Event()
        typing_task2 = asyncio.create_task(_keep_typing(bot, chat_id, stop_typing2))
        try:
            async with client_lock:
                response = await query_agent(client, f"[Voice message transcript]: {transcript}")
        finally:
            stop_typing2.set()
            await typing_task2

        await _send_parts(message, response)

    # ------------------------------------------------------------- Images
    @dp.message(whitelist, F.photo)
    async def handle_photo(message: Message) -> None:
        chat_id = message.chat.id
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing(bot, chat_id, stop_typing))

        try:
            photo = message.photo[-1]  # type: ignore[index]
            file = await bot.get_file(photo.file_id)
            bio = await bot.download_file(file.file_path)  # type: ignore[arg-type]
            image_bytes = bio.read()  # type: ignore[union-attr]
            image_b64 = base64.b64encode(image_bytes).decode("ascii")

            caption = message.caption or "What do you see in this image? Describe it and respond."

            async with client_lock:
                response = await query_agent_with_image(client, image_b64, "image/jpeg", caption)
        finally:
            stop_typing.set()
            await typing_task

        user_id = message.from_user.id if message.from_user else 0
        now = datetime.now(UTC).isoformat(timespec="seconds")
        entry = BufferEntry(
            ts=now,
            session=f"tg-image-{user_id}",
            content=f"[Image received] {response[:500]}",
            tags=("image",),
        )
        await buffer_store.append(entry)

        await _send_parts(message, response)

    # --------------------------------------------------------- Unsupported media
    @dp.message(
        whitelist,
        F.document
        | F.sticker
        | F.animation
        | F.video
        | F.video_note
        | F.audio
        | F.contact
        | F.location,
    )
    async def handle_unsupported_media(message: Message) -> None:
        await message.answer(
            "I can't process this type of media yet. I support text, voice messages, and photos."
        )

    # --------------------------------------------------------- Text (catch-all)
    @dp.message(whitelist)
    async def handle_message(message: Message) -> None:
        if not message.text:
            return

        chat_id = message.chat.id
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing(bot, chat_id, stop_typing))

        try:
            async with client_lock:
                response = await query_agent(client, message.text)
        finally:
            stop_typing.set()
            await typing_task

        await _send_parts(message, response)

    log.info("Starting Telegram bot polling (allowed IDs: %s)", allowed_ids)
    await dp.start_polling(bot)
