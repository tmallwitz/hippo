"""Short-term buffer store — append-only Markdown for raw impressions."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from hippo.memory.types import BufferEntry

# Regex to split buffer.md into individual entry sections
_ENTRY_SPLIT = re.compile(r"(?=^## )", re.MULTILINE)


def _entry_to_md(entry: BufferEntry) -> str:
    lines = [f"## {entry.ts}"]
    if entry.tags:
        lines.append(f"tags: {', '.join(entry.tags)}")
    lines.append("")
    lines.append(entry.content)
    lines.append("")
    return "\n".join(lines)


def _md_to_entry(section: str) -> BufferEntry | None:
    lines = section.strip().splitlines()
    if not lines or not lines[0].startswith("## "):
        return None
    ts = lines[0][3:].strip()
    tags: tuple[str, ...] = ()
    content_lines: list[str] = []
    past_header = False
    for line in lines[1:]:
        if not past_header and line.startswith("tags:"):
            raw = line[5:].strip()
            tags = tuple(t.strip() for t in raw.split(",") if t.strip())
        elif not past_header and line == "":
            past_header = True
        else:
            past_header = True
            content_lines.append(line)
    content = "\n".join(content_lines).strip()
    if not ts or not content:
        return None
    return BufferEntry(ts=ts, session="", content=content, tags=tags)


class ObsidianBufferStore:
    """Append-only Markdown buffer at ``short_term/buffer.md``.

    Entries are written during conversation without any upfront structure.
    The dream cycle reads and archives them. Human-readable in Obsidian.
    """

    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path
        self._lock = asyncio.Lock()
        short_term = vault_path / "short_term"
        short_term.mkdir(exist_ok=True)
        (short_term / "processed").mkdir(exist_ok=True)
        self._migrate_jsonl_if_needed()

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def append(self, entry: BufferEntry) -> None:
        """Append a single entry to the buffer."""
        async with self._lock:
            await asyncio.to_thread(self._append_sync, entry)

    async def read_buffer(self) -> tuple[BufferEntry, ...]:
        """Return all entries currently in the buffer."""
        async with self._lock:
            return await asyncio.to_thread(self._read_buffer_sync)

    async def archive_buffer(self, date: str) -> int:
        """Move buffer entries to ``short_term/processed/YYYY-MM-DD.md``.

        Appends to the processed file if it already exists (handles
        multiple dream runs on the same day). Clears the active buffer.

        Returns the number of entries archived.
        """
        async with self._lock:
            return await asyncio.to_thread(self._archive_buffer_sync, date)

    # ------------------------------------------------------------------
    # Synchronous helpers (called via asyncio.to_thread)
    # ------------------------------------------------------------------

    def _buffer_path(self) -> Path:
        return self._vault_path / "short_term" / "buffer.md"

    def _append_sync(self, entry: BufferEntry) -> None:
        path = self._buffer_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(_entry_to_md(entry))

    def _read_buffer_sync(self) -> tuple[BufferEntry, ...]:
        path = self._buffer_path()
        if not path.exists():
            return ()
        text = path.read_text(encoding="utf-8")
        entries: list[BufferEntry] = []
        for section in _ENTRY_SPLIT.split(text):
            entry = _md_to_entry(section)
            if entry is not None:
                entries.append(entry)
        return tuple(entries)

    def _archive_buffer_sync(self, date: str) -> int:
        path = self._buffer_path()
        if not path.exists():
            return 0
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return 0

        entries = [e for s in _ENTRY_SPLIT.split(text) if (e := _md_to_entry(s)) is not None]
        count = len(entries)
        if count == 0:
            return 0

        processed_path = self._vault_path / "short_term" / "processed" / f"{date}.md"
        with processed_path.open("a", encoding="utf-8") as f:
            f.write(text + "\n")

        path.write_text("", encoding="utf-8")
        return count

    def _migrate_jsonl_if_needed(self) -> None:
        """Migrate legacy buffer.jsonl to buffer.md if it exists."""
        jsonl_path = self._vault_path / "short_term" / "buffer.jsonl"
        if not jsonl_path.exists():
            return
        entries: list[BufferEntry] = []
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                # Skip debug entries written by debug_buffer.py
                if raw.get("session") == "debug":
                    continue
                entries.append(
                    BufferEntry(
                        ts=raw.get("ts", ""),
                        session=raw.get("session", ""),
                        content=raw.get("content", ""),
                        tags=tuple(raw.get("tags") or []),
                    )
                )
            except Exception:
                continue

        md_path = self._buffer_path()
        if entries:
            existing = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
            new_sections = "".join(_entry_to_md(e) for e in entries)
            md_path.write_text((existing + new_sections).lstrip(), encoding="utf-8")

        jsonl_path.unlink()
