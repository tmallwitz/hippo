"""Entry point for `uv run hippo <BotName>`."""

from __future__ import annotations

import argparse
import asyncio
import logging
import logging.handlers
import re
import sys
from pathlib import Path

_BOT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("hippo")


def _parse_args() -> str:
    parser = argparse.ArgumentParser(
        prog="hippo",
        description="Start a Hippo bot. Each bot runs as an independent process.",
    )
    parser.add_argument(
        "bot_name",
        help=(
            "Name of the bot to start (e.g., Alice). "
            "Must match a config block in .env (e.g., ALICE_TELEGRAM_BOT_TOKEN)."
        ),
    )
    args = parser.parse_args()
    if not _BOT_NAME_RE.match(args.bot_name):
        parser.error(
            f"Invalid bot name {args.bot_name!r}. "
            "Must start with a letter and contain only letters, digits, and underscores."
        )
    return str(args.bot_name)


def _add_file_handler(bot_name: str) -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    handler = logging.handlers.TimedRotatingFileHandler(
        logs_dir / f"{bot_name}.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    logging.getLogger().addHandler(handler)


def main() -> None:
    """Start the Hippo bot."""
    bot_name = _parse_args()
    _add_file_handler(bot_name)
    try:
        asyncio.run(_async_main(bot_name))
    except KeyboardInterrupt:
        log.info("Shutting down.")


async def _async_main(bot_name: str) -> None:
    from hippo.config import get_config

    try:
        config = get_config(bot_name)
    except Exception as exc:
        log.error("Failed to load config: %s", exc)
        sys.exit(1)

    log.info(
        "Config loaded — bot=%s vault=%s model=%s",
        config.hippo_bot_name,
        config.hippo_vault_path,
        config.hippo_model,
    )

    from hippo.setup import setup_vault

    setup_vault(config.hippo_vault_path)

    from aiogram import Bot

    from hippo.agent import create_agent
    from hippo.scheduler import run_scheduler
    from hippo.telegram_bridge import run_bot

    (
        client,
        scheduled_store,
        buffer_store,
        mailbox_store,
        semantic_store,
        episodic_store,
    ) = await create_agent(config)
    bot = Bot(token=config.telegram_bot_token)
    client_lock = asyncio.Lock()

    async with client:
        log.info("Agent connected. Starting Telegram bot + scheduler…")
        await asyncio.gather(
            run_bot(
                config,
                client,
                bot,
                client_lock,
                buffer_store,
                mailbox_store,
                scheduled_store,
                semantic_store,
                episodic_store,
            ),
            run_scheduler(
                config,
                client,
                client_lock,
                bot,
                scheduled_store,
                buffer_store,
                mailbox_store,
                episodic_store,
            ),
        )


if __name__ == "__main__":
    main()
