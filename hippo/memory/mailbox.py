"""Inter-bot mailbox store — Markdown messages in each bot's inbox/."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import frontmatter

from hippo.memory.types import MailboxMessage


def load_bot_registry(project_root: Path) -> dict[str, Path]:
    """Load the bot registry from ``bots.yaml`` in the project root.

    Returns a dict mapping bot names to their vault paths.
    Returns an empty dict if the file does not exist.
    """
    registry_path = project_root / "bots.yaml"
    if not registry_path.exists():
        return {}

    try:
        import yaml
    except ImportError:
        return {}

    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    bots = raw.get("bots", {})
    result: dict[str, Path] = {}
    for name, info in bots.items():
        if isinstance(info, dict) and "vault" in info:
            result[str(name)] = Path(info["vault"]).expanduser()
    return result


class ObsidianMailboxStore:
    """Filesystem mailbox for inter-bot messages.

    Each bot has an ``inbox/`` folder in its vault. Messages are
    stored as Markdown files with YAML frontmatter.
    """

    def __init__(self, vault_path: Path, bot_name: str) -> None:
        self._vault_path = vault_path
        self._bot_name = bot_name
        self._lock = asyncio.Lock()
        (vault_path / "inbox").mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def send_message(
        self,
        target_vault: Path,
        from_bot: str,
        subject: str,
        content: str,
        ts: str,
    ) -> Path:
        """Write a message into the target bot's inbox.

        Returns the path of the created message file.
        """
        async with self._lock:
            return await asyncio.to_thread(
                self._send_message_sync, target_vault, from_bot, subject, content, ts
            )

    async def read_inbox(self) -> tuple[MailboxMessage, ...]:
        """Return all messages in this bot's inbox, sorted by timestamp."""
        async with self._lock:
            return await asyncio.to_thread(self._read_inbox_sync)

    async def clear_inbox(self) -> int:
        """Delete all message files from the inbox.

        Returns the number of messages deleted.
        """
        async with self._lock:
            return await asyncio.to_thread(self._clear_inbox_sync)

    # ------------------------------------------------------------------
    # Synchronous helpers (called via asyncio.to_thread)
    # ------------------------------------------------------------------

    def _inbox_path(self, vault: Path | None = None) -> Path:
        target = vault if vault is not None else self._vault_path
        return target / "inbox"

    def _send_message_sync(
        self,
        target_vault: Path,
        from_bot: str,
        subject: str,
        content: str,
        ts: str,
    ) -> Path:
        inbox = self._inbox_path(target_vault)
        inbox.mkdir(parents=True, exist_ok=True)

        file_id = uuid.uuid4().hex[:8]
        filename = f"msg-{file_id}.md"
        path = inbox / filename

        post = frontmatter.Post(
            content,
            **{
                "from": from_bot,
                "to": self._bot_name,
                "ts": ts,
                "subject": subject,
            },
        )
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return path

    def _read_inbox_sync(self) -> tuple[MailboxMessage, ...]:
        inbox = self._inbox_path()
        messages: list[MailboxMessage] = []
        for path in sorted(inbox.rglob("*.md")):
            try:
                post = frontmatter.load(str(path))
                messages.append(
                    MailboxMessage(
                        from_bot=str(post.metadata.get("from", "")),
                        to_bot=str(post.metadata.get("to", self._bot_name)),
                        ts=str(post.metadata.get("ts", "")),
                        subject=str(post.metadata.get("subject", "")),
                        content=post.content,
                    )
                )
            except Exception:
                continue  # Skip malformed messages

        # Sort by timestamp (ISO strings sort lexicographically)
        messages.sort(key=lambda m: m.ts)
        return tuple(messages)

    def _clear_inbox_sync(self) -> int:
        inbox = self._inbox_path()
        count = 0
        for path in inbox.rglob("*.md"):
            path.unlink()
            count += 1
        return count
