"""Telegram bot bridge — connects aiogram to the Claude Agent SDK client."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from aiogram.enums import ChatAction
from aiogram.filters import BaseFilter
from aiogram.types import Message, MessageEntity
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock
from telegramify_markdown import convert
from telegramify_markdown.config import get_runtime_config

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeSDKClient

    from hippo.config import HippoConfig

log = logging.getLogger(__name__)

_TELEGRAM_MSG_LIMIT = 4096

# Configure telegramify-markdown for Claude-style output
_tg_cfg = get_runtime_config()
_tg_cfg.cite_expandable = True


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
# Agent query (public — also used by scheduler)
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


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------


async def run_bot(
    config: HippoConfig,
    client: ClaudeSDKClient,
    bot: Bot,
    client_lock: asyncio.Lock,
) -> None:
    """Start the Telegram bot and poll for messages."""
    dp = Dispatcher()

    allowed_ids = set(config.allowed_telegram_ids)
    whitelist = _WhitelistFilter(allowed_ids)

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

        for part in convert_to_telegram(response):
            try:
                await message.answer(
                    text=part["text"],  # type: ignore[arg-type]
                    entities=part["entities"],  # type: ignore[arg-type]
                )
            except Exception:
                await message.answer(str(part["text"]))

    log.info("Starting Telegram bot polling (allowed IDs: %s)", allowed_ids)
    await dp.start_polling(bot)
