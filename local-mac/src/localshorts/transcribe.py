from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo-q4"


def transcribe_video(
    video_path: Path,
    model: str = DEFAULT_MODEL,
    language: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    import mlx_whisper

    kwargs: dict[str, Any] = {
        "path_or_hf_repo": model,
        "verbose": None,
        "word_timestamps": False,
    }
    if language:
        kwargs["language"] = language

    result = mlx_whisper.transcribe(str(video_path), **kwargs)
    full_text = str(result.get("text") or "").strip()

    segments: list[dict[str, Any]] = []
    for raw in result.get("segments") or []:
        text = str(raw.get("text") or "").strip()
        try:
            start = float(raw.get("start", 0.0))
            end = float(raw.get("end", start))
        except (TypeError, ValueError):
            continue
        if end <= start:
            continue
        segments.append({"start": start, "end": end, "text": text})

    return full_text, segments
