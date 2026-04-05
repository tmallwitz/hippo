"""Tests for the dream cycle runner (orchestration layer, no LLM calls)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hippo.memory.buffer import ObsidianBufferStore
from hippo.memory.mailbox import ObsidianMailboxStore
from hippo.memory.types import BufferEntry


def _make_config(tmp_path: Path) -> MagicMock:
    config = MagicMock()
    config.hippo_vault_path = tmp_path
    config.hippo_dream_model = "claude-sonnet-4-5"
    config.hippo_bot_name = "alice"
    return config


@pytest.fixture()
def buffer_store(tmp_vault: Path) -> ObsidianBufferStore:
    return ObsidianBufferStore(tmp_vault)


@pytest.fixture()
def mailbox_store(tmp_vault: Path) -> ObsidianMailboxStore:
    return ObsidianMailboxStore(tmp_vault, "alice")


class TestEmptyBuffer:
    async def test_empty_buffer_skips_llm(
        self,
        tmp_vault: Path,
        buffer_store: ObsidianBufferStore,
        mailbox_store: ObsidianMailboxStore,
    ) -> None:
        config = _make_config(tmp_vault)
        from hippo.dream import runner

        runner._dream_running.clear()

        with patch("hippo.dream.runner.ClaudeSDKClient") as mock_client_cls:
            result = await runner.run_dream(config, buffer_store, mailbox_store)

        mock_client_cls.assert_not_called()
        assert "empty" in result.lower()

    async def test_empty_buffer_writes_report(
        self,
        tmp_vault: Path,
        buffer_store: ObsidianBufferStore,
        mailbox_store: ObsidianMailboxStore,
    ) -> None:
        config = _make_config(tmp_vault)
        from hippo.dream import runner

        runner._dream_running.clear()

        with patch("hippo.dream.runner.ClaudeSDKClient"):
            await runner.run_dream(config, buffer_store, mailbox_store)

        reports = list((tmp_vault / "dream_reports").glob("*.md"))
        assert len(reports) == 1


class TestConcurrentPrevention:
    async def test_concurrent_dream_returns_early(
        self,
        tmp_vault: Path,
        buffer_store: ObsidianBufferStore,
        mailbox_store: ObsidianMailboxStore,
    ) -> None:
        config = _make_config(tmp_vault)
        from hippo.dream import runner

        runner._dream_running.set()
        try:
            result = await runner.run_dream(config, buffer_store, mailbox_store)
            assert "already in progress" in result.lower()
        finally:
            runner._dream_running.clear()


class TestArchiveOnCompletion:
    async def test_buffer_archived_after_dream(
        self,
        tmp_vault: Path,
        buffer_store: ObsidianBufferStore,
        mailbox_store: ObsidianMailboxStore,
    ) -> None:
        config = _make_config(tmp_vault)
        await buffer_store.append(
            BufferEntry(ts="2026-04-05T10:00:00Z", session="tg-1", content="test entry")
        )

        from hippo.dream import runner

        runner._dream_running.clear()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.query = AsyncMock()
        mock_client.receive_response = MagicMock(return_value=_empty_async_gen())

        with (
            patch("hippo.dream.runner.ClaudeSDKClient", return_value=mock_client),
            patch("hippo.dream.runner.create_dream_server"),
        ):
            await runner.run_dream(config, buffer_store, mailbox_store)

        remaining = await buffer_store.read_buffer()
        assert remaining == ()

        processed = list((tmp_vault / "short_term" / "processed").glob("*.md"))
        assert len(processed) == 1

    async def test_inbox_cleared_after_dream(
        self,
        tmp_vault: Path,
        buffer_store: ObsidianBufferStore,
        mailbox_store: ObsidianMailboxStore,
    ) -> None:
        config = _make_config(tmp_vault)
        await buffer_store.append(
            BufferEntry(ts="2026-04-05T10:00:00Z", session="tg-1", content="something")
        )

        # Write a message directly into the inbox
        import frontmatter

        msg_path = tmp_vault / "inbox" / "msg-test.md"
        post = frontmatter.Post(
            "Hello alice",
            **{"from": "bob", "to": "alice", "ts": "2026-04-05T09:00:00Z", "subject": "Hi"},
        )
        msg_path.write_text(frontmatter.dumps(post), encoding="utf-8")

        from hippo.dream import runner

        runner._dream_running.clear()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.query = AsyncMock()
        mock_client.receive_response = MagicMock(return_value=_empty_async_gen())

        with (
            patch("hippo.dream.runner.ClaudeSDKClient", return_value=mock_client),
            patch("hippo.dream.runner.create_dream_server"),
        ):
            await runner.run_dream(config, buffer_store, mailbox_store)

        remaining = await mailbox_store.read_inbox()
        assert remaining == ()


class TestRawDocuments:
    def test_scan_finds_md_and_txt(self, tmp_vault: Path) -> None:
        from hippo.dream.runner import _scan_raw_documents

        (tmp_vault / "raw" / "note.md").write_text("# Hello\nsome content", encoding="utf-8")
        (tmp_vault / "raw" / "data.txt").write_text("plain text", encoding="utf-8")
        (tmp_vault / "raw" / "image.png").write_bytes(b"\x89PNG")

        docs = _scan_raw_documents(tmp_vault)
        names = [name for name, _ in docs]
        assert "note.md" in names
        assert "data.txt" in names
        assert "image.png" not in names

    def test_scan_ignores_processed_subdir(self, tmp_vault: Path) -> None:
        from hippo.dream.runner import _scan_raw_documents

        (tmp_vault / "raw" / "active.md").write_text("active", encoding="utf-8")
        (tmp_vault / "raw" / "processed" / "old.md").write_text("old", encoding="utf-8")

        docs = _scan_raw_documents(tmp_vault)
        names = [name for name, _ in docs]
        assert "active.md" in names
        assert "old.md" not in names

    def test_scan_returns_empty_when_no_raw_dir(self, tmp_vault: Path) -> None:
        import shutil

        from hippo.dream.runner import _scan_raw_documents

        shutil.rmtree(tmp_vault / "raw")
        assert _scan_raw_documents(tmp_vault) == []

    def test_move_to_processed(self, tmp_vault: Path) -> None:
        from hippo.dream.runner import _move_raw_to_processed

        (tmp_vault / "raw" / "doc.md").write_text("content", encoding="utf-8")

        moved = _move_raw_to_processed(tmp_vault, ["doc.md"])
        assert moved == 1
        assert not (tmp_vault / "raw" / "doc.md").exists()
        assert (tmp_vault / "raw" / "processed" / "doc.md").exists()

    def test_format_truncates_large_files(self) -> None:
        from hippo.dream.runner import _format_raw_documents

        large = "x" * 20_000
        result = _format_raw_documents([("big.md", large)])
        assert "[...truncated]" in result
        assert len(result) < 15_000


class TestReportAppend:
    def test_first_run_creates_file_with_frontmatter(self, tmp_vault: Path) -> None:
        from hippo.dream.runner import _write_dream_report

        _write_dream_report(tmp_vault, "2026-04-05", "First run content", is_empty=False)

        report = (tmp_vault / "dream_reports" / "2026-04-05.md").read_text(encoding="utf-8")
        assert "First run content" in report
        assert "2026-04-05" in report

    def test_second_run_appends_with_separator(self, tmp_vault: Path) -> None:
        from hippo.dream.runner import _write_dream_report

        _write_dream_report(tmp_vault, "2026-04-05", "First run content", is_empty=False)
        _write_dream_report(tmp_vault, "2026-04-05", "Second run content", is_empty=False)

        report = (tmp_vault / "dream_reports" / "2026-04-05.md").read_text(encoding="utf-8")
        assert "First run content" in report
        assert "Second run content" in report
        assert "---" in report

    def test_only_one_file_per_day(self, tmp_vault: Path) -> None:
        from hippo.dream.runner import _write_dream_report

        _write_dream_report(tmp_vault, "2026-04-05", "Run 1", is_empty=False)
        _write_dream_report(tmp_vault, "2026-04-05", "Run 2", is_empty=False)
        _write_dream_report(tmp_vault, "2026-04-05", "Run 3", is_empty=False)

        reports = list((tmp_vault / "dream_reports").glob("*.md"))
        assert len(reports) == 1


async def _empty_async_gen():  # type: ignore[return]
    """Async generator that yields nothing (simulates empty agent response)."""
    return
    yield  # make it a generator
