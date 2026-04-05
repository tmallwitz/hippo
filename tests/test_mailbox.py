"""Tests for ObsidianMailboxStore and load_bot_registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from hippo.memory.mailbox import ObsidianMailboxStore, load_bot_registry


@pytest.fixture()
def alice_store(tmp_vault: Path) -> ObsidianMailboxStore:
    return ObsidianMailboxStore(tmp_vault, "alice")


@pytest.fixture()
def bob_vault(tmp_path: Path) -> Path:
    bob = tmp_path / "bob-vault"
    bob.mkdir()
    (bob / "inbox").mkdir()
    return bob


class TestSendMessage:
    async def test_creates_file_in_target_inbox(
        self, alice_store: ObsidianMailboxStore, bob_vault: Path
    ) -> None:
        await alice_store.send_message(
            target_vault=bob_vault,
            from_bot="alice",
            subject="Hello",
            content="Just checking in.",
            ts="2026-04-05T10:00:00Z",
        )
        files = list((bob_vault / "inbox").glob("*.md"))
        assert len(files) == 1

    async def test_frontmatter_fields(
        self, alice_store: ObsidianMailboxStore, bob_vault: Path
    ) -> None:
        import frontmatter

        await alice_store.send_message(
            target_vault=bob_vault,
            from_bot="alice",
            subject="Test subject",
            content="Test content.",
            ts="2026-04-05T10:00:00Z",
        )
        path = next(iter((bob_vault / "inbox").glob("*.md")))
        post = frontmatter.load(str(path))
        assert post.metadata["from"] == "alice"
        assert post.metadata["subject"] == "Test subject"
        assert post.metadata["ts"] == "2026-04-05T10:00:00Z"
        assert post.content == "Test content."

    async def test_unique_filenames(
        self, alice_store: ObsidianMailboxStore, bob_vault: Path
    ) -> None:
        for i in range(3):
            await alice_store.send_message(
                target_vault=bob_vault,
                from_bot="alice",
                subject=f"msg {i}",
                content="body",
                ts=f"2026-04-05T10:0{i}:00Z",
            )
        files = list((bob_vault / "inbox").glob("*.md"))
        assert len(files) == 3


class TestReadInbox:
    async def test_empty_inbox(self, alice_store: ObsidianMailboxStore) -> None:
        result = await alice_store.read_inbox()
        assert result == ()

    async def test_reads_messages(
        self, alice_store: ObsidianMailboxStore, tmp_vault: Path, bob_vault: Path
    ) -> None:
        bob_store = ObsidianMailboxStore(bob_vault, "bob")
        await bob_store.send_message(
            target_vault=tmp_vault,
            from_bot="bob",
            subject="Hi alice",
            content="Hello!",
            ts="2026-04-05T10:00:00Z",
        )
        messages = await alice_store.read_inbox()
        assert len(messages) == 1
        assert messages[0].from_bot == "bob"
        assert messages[0].subject == "Hi alice"
        assert messages[0].content == "Hello!"

    async def test_sorted_by_timestamp(
        self, alice_store: ObsidianMailboxStore, tmp_vault: Path, bob_vault: Path
    ) -> None:
        bob_store = ObsidianMailboxStore(bob_vault, "bob")
        for ts in ["2026-04-05T12:00:00Z", "2026-04-05T08:00:00Z", "2026-04-05T10:00:00Z"]:
            await bob_store.send_message(
                target_vault=tmp_vault,
                from_bot="bob",
                subject=f"msg at {ts}",
                content="body",
                ts=ts,
            )
        messages = await alice_store.read_inbox()
        assert messages[0].ts == "2026-04-05T08:00:00Z"
        assert messages[1].ts == "2026-04-05T10:00:00Z"
        assert messages[2].ts == "2026-04-05T12:00:00Z"


class TestClearInbox:
    async def test_clear_empty_returns_zero(self, alice_store: ObsidianMailboxStore) -> None:
        count = await alice_store.clear_inbox()
        assert count == 0

    async def test_clear_removes_files(
        self, alice_store: ObsidianMailboxStore, tmp_vault: Path, bob_vault: Path
    ) -> None:
        bob_store = ObsidianMailboxStore(bob_vault, "bob")
        for i in range(3):
            await bob_store.send_message(
                target_vault=tmp_vault,
                from_bot="bob",
                subject=f"msg {i}",
                content="body",
                ts=f"2026-04-05T10:0{i}:00Z",
            )
        count = await alice_store.clear_inbox()
        assert count == 3
        remaining = await alice_store.read_inbox()
        assert remaining == ()


class TestLoadBotRegistry:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = load_bot_registry(tmp_path)
        assert result == {}

    def test_loads_registry(self, tmp_path: Path) -> None:
        (tmp_path / "bots.yaml").write_text(
            "bots:\n  alice:\n    vault: /tmp/alice\n    role: test\n",
            encoding="utf-8",
        )
        result = load_bot_registry(tmp_path)
        assert "alice" in result
        assert result["alice"] == Path("/tmp/alice")

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "bots.yaml").write_text("", encoding="utf-8")
        result = load_bot_registry(tmp_path)
        assert result == {}
