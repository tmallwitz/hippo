"""Tests for ObsidianEpisodicStore."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import frontmatter
import pytest

from hippo.memory.episodic import ObsidianEpisodicStore


@pytest.fixture()
def store(tmp_vault: Path) -> ObsidianEpisodicStore:
    return ObsidianEpisodicStore(tmp_vault)


def _ts(date: str, time: str) -> datetime:
    """Helper to create a datetime from date and time strings."""
    return datetime.fromisoformat(f"{date}T{time}:00")


# ---------------------------------------------------------------------------
# log_episode
# ---------------------------------------------------------------------------


class TestLogEpisode:
    async def test_creates_daily_note(self, store: ObsidianEpisodicStore, tmp_vault: Path) -> None:
        ep = await store.log_episode(
            "Test episode", "Some content", tags=["test"], timestamp=_ts("2026-04-05", "14:30")
        )
        path = tmp_vault / "episodic" / "2026-04-05.md"
        assert path.exists()
        assert ep.date == "2026-04-05"
        assert ep.time == "14:30"

    async def test_returns_episode(self, store: ObsidianEpisodicStore) -> None:
        ep = await store.log_episode(
            "My title", "My content", tags=["a", "b"], timestamp=_ts("2026-04-05", "10:00")
        )
        assert ep.title == "My title"
        assert ep.content == "My content"
        assert ep.tags == ("a", "b")

    async def test_multiple_same_day(self, store: ObsidianEpisodicStore, tmp_vault: Path) -> None:
        await store.log_episode("First", "Content 1", timestamp=_ts("2026-04-05", "09:00"))
        await store.log_episode("Second", "Content 2", timestamp=_ts("2026-04-05", "10:00"))
        await store.log_episode("Third", "Content 3", timestamp=_ts("2026-04-05", "11:00"))

        path = tmp_vault / "episodic" / "2026-04-05.md"
        post = frontmatter.load(str(path))
        assert post.metadata["episodes"] == 3
        assert "## 09:00" in post.content
        assert "## 10:00" in post.content
        assert "## 11:00" in post.content

    async def test_no_tags(self, store: ObsidianEpisodicStore, tmp_vault: Path) -> None:
        ep = await store.log_episode("No tags", "Content", timestamp=_ts("2026-04-05", "12:00"))
        assert ep.tags == ()

        path = tmp_vault / "episodic" / "2026-04-05.md"
        content = path.read_text(encoding="utf-8")
        assert "tags:" not in content


# ---------------------------------------------------------------------------
# recall_episodes
# ---------------------------------------------------------------------------


class TestRecallEpisodes:
    async def test_recall_date_range(self, store: ObsidianEpisodicStore) -> None:
        await store.log_episode("Day 1", "Content", timestamp=_ts("2026-04-01", "10:00"))
        await store.log_episode("Day 2", "Content", timestamp=_ts("2026-04-02", "10:00"))
        await store.log_episode("Day 3", "Content", timestamp=_ts("2026-04-03", "10:00"))

        result = await store.recall_episodes(start_date="2026-04-01", end_date="2026-04-02")
        assert len(result) == 2
        assert result[0].title == "Day 1"
        assert result[1].title == "Day 2"

    async def test_recall_text_query(self, store: ObsidianEpisodicStore) -> None:
        await store.log_episode(
            "Hippo planning", "Discussed architecture", timestamp=_ts("2026-04-05", "10:00")
        )
        await store.log_episode("Lunch break", "Had pizza", timestamp=_ts("2026-04-05", "12:00"))

        result = await store.recall_episodes(
            start_date="2026-04-05", end_date="2026-04-05", query="architecture"
        )
        assert len(result) == 1
        assert result[0].title == "Hippo planning"

    async def test_recall_searches_title(self, store: ObsidianEpisodicStore) -> None:
        await store.log_episode(
            "Important decision", "Details here", timestamp=_ts("2026-04-05", "10:00")
        )
        result = await store.recall_episodes(
            start_date="2026-04-05", end_date="2026-04-05", query="decision"
        )
        assert len(result) == 1

    async def test_recall_searches_tags(self, store: ObsidianEpisodicStore) -> None:
        await store.log_episode(
            "Meeting",
            "Discussed roadmap",
            tags=["projekt", "planung"],
            timestamp=_ts("2026-04-05", "10:00"),
        )
        result = await store.recall_episodes(
            start_date="2026-04-05", end_date="2026-04-05", query="planung"
        )
        assert len(result) == 1

    async def test_recall_date_and_query(self, store: ObsidianEpisodicStore) -> None:
        await store.log_episode("A", "Python stuff", timestamp=_ts("2026-04-01", "10:00"))
        await store.log_episode("B", "Python stuff", timestamp=_ts("2026-04-03", "10:00"))

        result = await store.recall_episodes(
            start_date="2026-04-02", end_date="2026-04-03", query="python"
        )
        assert len(result) == 1
        assert result[0].title == "B"

    async def test_recall_empty(self, store: ObsidianEpisodicStore) -> None:
        result = await store.recall_episodes(start_date="2026-04-01", end_date="2026-04-01")
        assert result == []


# ---------------------------------------------------------------------------
# Daily note format
# ---------------------------------------------------------------------------


class TestDailyNoteFormat:
    async def test_frontmatter_date(self, store: ObsidianEpisodicStore, tmp_vault: Path) -> None:
        await store.log_episode("Test", "Content", timestamp=_ts("2026-04-05", "10:00"))
        path = tmp_vault / "episodic" / "2026-04-05.md"
        post = frontmatter.load(str(path))
        assert str(post.metadata["date"]) == "2026-04-05"

    async def test_frontmatter_count(self, store: ObsidianEpisodicStore, tmp_vault: Path) -> None:
        await store.log_episode("A", "Content", timestamp=_ts("2026-04-05", "10:00"))
        await store.log_episode("B", "Content", timestamp=_ts("2026-04-05", "11:00"))

        path = tmp_vault / "episodic" / "2026-04-05.md"
        post = frontmatter.load(str(path))
        assert post.metadata["episodes"] == 2

    async def test_h2_format(self, store: ObsidianEpisodicStore, tmp_vault: Path) -> None:
        await store.log_episode("My Title", "Content", timestamp=_ts("2026-04-05", "14:32"))
        path = tmp_vault / "episodic" / "2026-04-05.md"
        content = path.read_text(encoding="utf-8")
        assert "## 14:32 — My Title" in content

    async def test_content_preserved(self, store: ObsidianEpisodicStore) -> None:
        multiline = "Line one\nLine two\n\nParagraph two with *markdown*"
        await store.log_episode("Multi-line", multiline, timestamp=_ts("2026-04-05", "10:00"))
        result = await store.recall_episodes(start_date="2026-04-05", end_date="2026-04-05")
        assert result[0].content == multiline


# ---------------------------------------------------------------------------
# Manual edits + roundtrip
# ---------------------------------------------------------------------------


class TestManualEditsAndRoundtrip:
    async def test_manual_edit_picked_up(
        self, store: ObsidianEpisodicStore, tmp_vault: Path
    ) -> None:
        await store.log_episode(
            "Original", "Original content", timestamp=_ts("2026-04-05", "10:00")
        )
        path = tmp_vault / "episodic" / "2026-04-05.md"

        # Simulate Obsidian edit
        text = path.read_text(encoding="utf-8")
        text = text.replace("Original content", "Edited content")
        path.write_text(text, encoding="utf-8")

        result = await store.recall_episodes(start_date="2026-04-05", end_date="2026-04-05")
        assert result[0].content == "Edited content"

    async def test_manually_created_note(
        self, store: ObsidianEpisodicStore, tmp_vault: Path
    ) -> None:
        """A daily note created by hand in Obsidian should be parseable."""
        path = tmp_vault / "episodic" / "2026-03-15.md"
        path.write_text(
            "---\ndate: 2026-03-15\nepisodes: 1\n---\n\n# 2026-03-15\n\n"
            "## 09:00 — Morning standup\n"
            "tags: work, meeting\n"
            "Discussed sprint goals for the week.\n",
            encoding="utf-8",
        )

        result = await store.recall_episodes(start_date="2026-03-15", end_date="2026-03-15")
        assert len(result) == 1
        assert result[0].title == "Morning standup"
        assert result[0].tags == ("work", "meeting")
        assert "sprint goals" in result[0].content

    async def test_roundtrip(self, store: ObsidianEpisodicStore) -> None:
        await store.log_episode(
            "Roundtrip test",
            "This should survive a write-read cycle.",
            tags=["test", "roundtrip"],
            timestamp=_ts("2026-04-05", "15:00"),
        )
        result = await store.recall_episodes(start_date="2026-04-05", end_date="2026-04-05")
        assert len(result) == 1
        ep = result[0]
        assert ep.title == "Roundtrip test"
        assert ep.content == "This should survive a write-read cycle."
        assert ep.tags == ("test", "roundtrip")
        assert ep.date == "2026-04-05"
        assert ep.time == "15:00"
