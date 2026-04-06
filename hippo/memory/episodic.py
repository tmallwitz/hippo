"""Obsidian-vault-backed episodic memory store (daily notes as Markdown files)."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import frontmatter

from hippo.memory.types import Episode

log = logging.getLogger(__name__)

_H2_RE = re.compile(
    r"^##\s+(\d{2}:\d{2})\s*[—–\-]\s*(.+)$",  # noqa: RUF001  # em-dash, en-dash, hyphen
    re.MULTILINE,
)
_TAGS_RE = re.compile(r"^\s*tags:\s*(.+)$", re.IGNORECASE)

_DEFAULT_LOOKBACK_DAYS = 7


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _daily_note_path(vault_path: Path, date_str: str) -> Path:
    return vault_path / "episodic" / f"{date_str}.md"


def _parse_daily_note(path: Path) -> list[Episode]:
    """Parse a daily note file into a list of Episodes."""
    post = frontmatter.load(str(path))
    note_date = str(post.metadata.get("date", path.stem))

    episodes: list[Episode] = []
    content = post.content

    # Find all H2 headings and their positions
    matches = list(_H2_RE.finditer(content))
    if not matches:
        return episodes

    for i, match in enumerate(matches):
        time_str = match.group(1)
        title = match.group(2).strip()

        # Extract section body (between this H2 and the next, or end of file)
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[body_start:body_end].strip()

        # Parse tags from first non-empty line if it starts with "tags:"
        tags: tuple[str, ...] = ()
        episode_content = body
        lines = body.split("\n")
        for j, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            tag_match = _TAGS_RE.match(stripped)
            if tag_match:
                raw_tags = tag_match.group(1)
                tags = tuple(t.strip() for t in raw_tags.split(",") if t.strip())
                # Content is everything after the tags line
                episode_content = "\n".join(lines[j + 1 :]).strip()
            break

        episodes.append(
            Episode(
                date=note_date,
                time=time_str,
                title=title,
                content=episode_content,
                tags=tags,
            )
        )

    return episodes


def _format_episode_section(episode: Episode) -> str:
    """Render an Episode as an H2 Markdown section."""
    lines = [f"## {episode.time} — {episode.title}"]
    if episode.tags:
        lines.append(f"tags: {', '.join(episode.tags)}")
    lines.append(episode.content)
    return "\n".join(lines)


def _write_daily_note(path: Path, date_str: str, episodes: list[Episode]) -> None:
    """Write a complete daily note file."""
    meta = {
        "date": date_str,
        "episodes": len(episodes),
    }

    sections = [f"# {date_str}", ""]
    for ep in episodes:
        sections.append(_format_episode_section(ep))
        sections.append("")

    post = frontmatter.Post("\n".join(sections), **meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")


def _append_episode_sync(vault_path: Path, episode: Episode) -> None:
    """Append an episode to the daily note, creating the file if needed."""
    path = _daily_note_path(vault_path, episode.date)

    if path.exists():
        existing = _parse_daily_note(path)
        existing.append(episode)
        _write_daily_note(path, episode.date, existing)
    else:
        _write_daily_note(path, episode.date, [episode])


def _load_episodes_in_range(vault_path: Path, start: date, end: date) -> list[Episode]:
    """Load all episodes from daily notes within the date range (inclusive)."""
    episodes: list[Episode] = []
    current = start
    while current <= end:
        date_str = current.isoformat()
        path = _daily_note_path(vault_path, date_str)
        if path.exists():
            try:
                episodes.extend(_parse_daily_note(path))
            except Exception:
                log.warning("Skipping unparseable daily note: %s", path)
        current += timedelta(days=1)
    return episodes


# ---------------------------------------------------------------------------
# Public store class
# ---------------------------------------------------------------------------


class ObsidianEpisodicStore:
    """Episodic journal memory backed by daily note Markdown files."""

    def __init__(self, vault_path: Path) -> None:
        self._vault = vault_path
        self._lock = asyncio.Lock()
        (vault_path / "episodic").mkdir(parents=True, exist_ok=True)

    async def log_episode(
        self,
        title: str,
        content: str,
        tags: list[str] | None = None,
        timestamp: datetime | None = None,
    ) -> Episode:
        """Append a new episode to today's daily note."""
        async with self._lock:
            return await asyncio.to_thread(self._log_episode_sync, title, content, tags, timestamp)

    def _log_episode_sync(
        self,
        title: str,
        content: str,
        tags: list[str] | None,
        timestamp: datetime | None,
    ) -> Episode:
        now = timestamp or datetime.now()
        episode = Episode(
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M"),
            title=title,
            content=content,
            tags=tuple(tags or []),
        )
        _append_episode_sync(self._vault, episode)
        return episode

    async def find_archivable_notes(
        self,
        max_age_days: int = 30,
        min_size_chars: int = 2000,
    ) -> list[tuple[str, Path]]:
        """Return daily notes that are old and large enough to be summarized.

        Returns list of (date_str, path) sorted by date ascending.
        """
        return await asyncio.to_thread(
            self._find_archivable_notes_sync, max_age_days, min_size_chars
        )

    def _find_archivable_notes_sync(
        self, max_age_days: int, min_size_chars: int
    ) -> list[tuple[str, Path]]:
        episodic_dir = self._vault / "episodic"
        if not episodic_dir.is_dir():
            return []
        cutoff = date.today() - timedelta(days=max_age_days)
        results: list[tuple[str, Path]] = []
        for md_file in episodic_dir.glob("*.md"):
            try:
                note_date = date.fromisoformat(md_file.stem)
            except ValueError:
                continue  # not a YYYY-MM-DD filename
            if note_date >= cutoff:
                continue  # too recent
            try:
                size = len(md_file.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if size < min_size_chars:
                continue
            results.append((md_file.stem, md_file))
        results.sort(key=lambda x: x[0])
        return results

    async def archive_daily_note(self, date_str: str, summary_content: str) -> None:
        """Archive a daily note: move original to episodic/archive/, write summary.

        The original verbose note is preserved in the archive directory.
        The summary replaces the active daily note.
        """
        async with self._lock:
            await asyncio.to_thread(self._archive_daily_note_sync, date_str, summary_content)

    def _archive_daily_note_sync(self, date_str: str, summary_content: str) -> None:
        original_path = _daily_note_path(self._vault, date_str)
        if not original_path.exists():
            log.debug("archive_daily_note: no file for %s, skipping", date_str)
            return
        archive_dir = self._vault / "episodic" / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"{date_str}.md"
        original_path.rename(archive_path)

        # Write condensed summary as the new active daily note
        meta = {
            "date": date_str,
            "archived": True,
            "archive_path": str(archive_path),
        }
        post = frontmatter.Post(
            f"# {date_str} (summary)\n\n{summary_content}",
            **meta,
        )
        original_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        log.info("Archived daily note %s (%d chars summary)", date_str, len(summary_content))

    async def recall_episodes(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        query: str | None = None,
    ) -> list[Episode]:
        """Retrieve episodes filtered by date range and/or text query."""
        return await asyncio.to_thread(self._recall_episodes_sync, start_date, end_date, query)

    def _recall_episodes_sync(
        self,
        start_date: str | None,
        end_date: str | None,
        query: str | None,
    ) -> list[Episode]:
        today = date.today()

        end = date.fromisoformat(end_date) if end_date else today
        start = (
            date.fromisoformat(start_date)
            if start_date
            else end - timedelta(days=_DEFAULT_LOOKBACK_DAYS)
        )

        episodes = _load_episodes_in_range(self._vault, start, end)

        if query:
            q = query.lower()
            episodes = [
                ep
                for ep in episodes
                if q in ep.title.lower()
                or q in ep.content.lower()
                or any(q in tag.lower() for tag in ep.tags)
            ]

        return episodes
