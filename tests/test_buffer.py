"""Tests for ObsidianBufferStore."""

from __future__ import annotations

from pathlib import Path

import pytest

from hippo.memory.buffer import ObsidianBufferStore, _entry_to_md, _md_to_entry
from hippo.memory.types import BufferEntry


@pytest.fixture()
def store(tmp_vault: Path) -> ObsidianBufferStore:
    return ObsidianBufferStore(tmp_vault)


class TestAppend:
    async def test_append_creates_file(self, store: ObsidianBufferStore, tmp_vault: Path) -> None:
        entry = BufferEntry(ts="2026-04-05T10:00:00Z", session="tg-alice", content="hello")
        await store.append(entry)
        path = tmp_vault / "short_term" / "buffer.md"
        assert path.exists()
        assert "hello" in path.read_text(encoding="utf-8")

    async def test_append_multiple(self, store: ObsidianBufferStore, tmp_vault: Path) -> None:
        for i in range(3):
            await store.append(
                BufferEntry(ts=f"2026-04-05T10:0{i}:00Z", session="s", content=f"entry {i}")
            )
        text = (tmp_vault / "short_term" / "buffer.md").read_text(encoding="utf-8")
        assert text.count("## 2026") == 3

    async def test_append_tags(self, store: ObsidianBufferStore, tmp_vault: Path) -> None:
        entry = BufferEntry(
            ts="2026-04-05T10:00:00Z",
            session="s",
            content="prefers dark mode",
            tags=("preference", "ui"),
        )
        await store.append(entry)
        text = (tmp_vault / "short_term" / "buffer.md").read_text(encoding="utf-8")
        assert "tags: preference, ui" in text

    async def test_append_roundtrip(self, store: ObsidianBufferStore) -> None:
        entry = BufferEntry(
            ts="2026-04-05T12:00:00Z",
            session="tg-alice",
            content="uses uv not pip",
            tags=("tooling",),
        )
        await store.append(entry)
        entries = await store.read_buffer()
        assert len(entries) == 1
        assert entries[0].content == "uses uv not pip"
        assert entries[0].tags == ("tooling",)


class TestReadBuffer:
    async def test_empty_returns_empty_tuple(self, store: ObsidianBufferStore) -> None:
        assert await store.read_buffer() == ()

    async def test_missing_file_returns_empty(
        self, store: ObsidianBufferStore, tmp_vault: Path
    ) -> None:
        assert not (tmp_vault / "short_term" / "buffer.md").exists()
        assert await store.read_buffer() == ()

    async def test_read_order_preserved(self, store: ObsidianBufferStore) -> None:
        for i in range(5):
            await store.append(
                BufferEntry(ts=f"2026-04-05T10:0{i}:00Z", session="s", content=f"msg {i}")
            )
        entries = await store.read_buffer()
        assert [e.content for e in entries] == [f"msg {i}" for i in range(5)]


class TestArchiveBuffer:
    async def test_archive_moves_entries(
        self, store: ObsidianBufferStore, tmp_vault: Path
    ) -> None:
        await store.append(BufferEntry(ts="2026-04-05T10:00:00Z", session="s", content="a"))
        await store.append(BufferEntry(ts="2026-04-05T10:01:00Z", session="s", content="b"))
        count = await store.archive_buffer("2026-04-05")
        assert count == 2
        processed = tmp_vault / "short_term" / "processed" / "2026-04-05.md"
        assert processed.exists()
        text = processed.read_text(encoding="utf-8")
        assert "## 2026" in text

    async def test_archive_clears_active_buffer(
        self, store: ObsidianBufferStore, tmp_vault: Path
    ) -> None:
        await store.append(BufferEntry(ts="2026-04-05T10:00:00Z", session="s", content="x"))
        await store.archive_buffer("2026-04-05")
        assert await store.read_buffer() == ()

    async def test_archive_appends_on_same_day(
        self, store: ObsidianBufferStore, tmp_vault: Path
    ) -> None:
        await store.append(BufferEntry(ts="2026-04-05T10:00:00Z", session="s", content="first"))
        await store.archive_buffer("2026-04-05")
        await store.append(BufferEntry(ts="2026-04-05T11:00:00Z", session="s", content="second"))
        await store.archive_buffer("2026-04-05")
        processed = tmp_vault / "short_term" / "processed" / "2026-04-05.md"
        text = processed.read_text(encoding="utf-8")
        assert "first" in text
        assert "second" in text

    async def test_archive_empty_buffer_returns_zero(self, store: ObsidianBufferStore) -> None:
        assert await store.archive_buffer("2026-04-05") == 0


class TestMarkdownFormat:
    def test_entry_to_md_with_tags(self) -> None:
        entry = BufferEntry(ts="2026-04-05T10:00:00Z", session="s", content="test", tags=("a",))
        md = _entry_to_md(entry)
        assert md.startswith("## 2026-04-05T10:00:00Z\n")
        assert "tags: a\n" in md
        assert "test" in md

    def test_entry_to_md_no_tags(self) -> None:
        entry = BufferEntry(ts="2026-04-05T10:00:00Z", session="s", content="test")
        md = _entry_to_md(entry)
        assert "tags:" not in md
        assert "test" in md

    def test_md_to_entry_roundtrip(self) -> None:
        entry = BufferEntry(
            ts="2026-04-05T10:00:00Z", session="s", content="hello world", tags=("x", "y")
        )
        md = _entry_to_md(entry)
        parsed = _md_to_entry(md)
        assert parsed is not None
        assert parsed.content == "hello world"
        assert parsed.tags == ("x", "y")
        assert parsed.ts == "2026-04-05T10:00:00Z"

    def test_md_to_entry_invalid_returns_none(self) -> None:
        assert _md_to_entry("not a valid section") is None
        assert _md_to_entry("") is None


class TestMigration:
    def test_migrates_jsonl_to_md(self, tmp_vault: Path) -> None:
        import json

        jsonl = tmp_vault / "short_term" / "buffer.jsonl"
        jsonl.write_text(
            json.dumps({"ts": "2026-04-05T10:00:00Z", "session": "tg-alice",
                        "content": "migrated entry", "tags": ["test"]}) + "\n",
            encoding="utf-8",
        )
        ObsidianBufferStore(tmp_vault)
        md = tmp_vault / "short_term" / "buffer.md"
        assert md.exists()
        assert not jsonl.exists()
        assert "migrated entry" in md.read_text(encoding="utf-8")

    def test_skips_debug_entries(self, tmp_vault: Path) -> None:
        import json

        jsonl = tmp_vault / "short_term" / "buffer.jsonl"
        jsonl.write_text(
            json.dumps({"ts": "2026-01-01T00:00:00Z", "session": "debug",
                        "content": "DEBUG TEST ENTRY", "tags": []}) + "\n",
            encoding="utf-8",
        )
        ObsidianBufferStore(tmp_vault)  # triggers migration
        md = tmp_vault / "short_term" / "buffer.md"
        assert not md.exists() or "DEBUG TEST ENTRY" not in md.read_text(encoding="utf-8")
