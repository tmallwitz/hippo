"""Entry point for `uv run hippo`."""

from __future__ import annotations

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("hippo")


def main() -> None:
    """Start the Hippo bot."""
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        log.info("Shutting down.")


async def _async_main() -> None:
    from hippo.config import get_config

    try:
        config = get_config()
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

    client, scheduled_store, buffer_store, mailbox_store = await create_agent(config)
    bot = Bot(token=config.telegram_bot_token)
    client_lock = asyncio.Lock()

    async with client:
        log.info("Agent connected. Starting Telegram bot + scheduler…")
        await asyncio.gather(
            run_bot(config, client, bot, client_lock, buffer_store, mailbox_store),
            run_scheduler(
                config, client, client_lock, bot, scheduled_store, buffer_store, mailbox_store
            ),
        )


if __name__ == "__main__":
    main()
