# Standards for Phase 5: Telegram Upgrade

## global/coding-style

- Type hints on all function signatures
- Async/await for all I/O operations
- Small, focused functions — each handler does one thing
- No dead code or commented-out blocks

## global/tech-stack

- **Package manager**: `uv` only — never `pip`
- **Telegram**: `aiogram` v3 patterns — `F.voice`, `F.photo` filters, `Command()` filter
- **New dependency**: `openai-whisper` (brings `torch` as transitive dep)
- **System dependency**: `ffmpeg` required on host for whisper

## global/conventions

- Conventional Commits: `feat(telegram): ...`
- Feature branch, squash-merge to main
- No private data in code or commits
