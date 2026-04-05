"""Local Whisper transcription for voice messages."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from typing import Any

log = logging.getLogger(__name__)

# Lazy-loaded whisper model singleton: (model_name, model_object)
_loaded: tuple[str, Any] | None = None


def _load_model(model_name: str) -> Any:
    import whisper  # type: ignore[import]

    global _loaded
    if _loaded is None or _loaded[0] != model_name:
        log.info("Loading Whisper model '%s'…", model_name)
        _loaded = (model_name, whisper.load_model(model_name))
    return _loaded[1]


def _transcribe_sync(audio_bytes: bytes, model_name: str, language: str | None) -> str:
    model = _load_model(model_name)
    # delete=False: on Windows, NamedTemporaryFile holds an exclusive lock while
    # open, which prevents ffmpeg from reading the file. We must close it before
    # passing the path to Whisper, then clean up manually.
    tmp_path = tempfile.mktemp(suffix=".ogg")  # intentional: need close-before-read on Windows
    try:
        with open(tmp_path, "wb") as f:
            f.write(audio_bytes)
        kwargs: dict[str, Any] = {}
        if language:
            kwargs["language"] = language
        result: dict[str, Any] = model.transcribe(tmp_path, **kwargs)  # type: ignore[assignment]
    finally:
        os.unlink(tmp_path)
    return str(result.get("text", "")).strip()


async def transcribe(
    audio_bytes: bytes,
    model_name: str = "base",
    language: str | None = None,
) -> str:
    """Transcribe audio bytes using local Whisper. Non-blocking via thread pool."""
    return await asyncio.to_thread(_transcribe_sync, audio_bytes, model_name, language)
