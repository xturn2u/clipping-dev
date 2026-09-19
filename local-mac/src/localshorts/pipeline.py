from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from .download import resolve_source
from .highlights import select_highlights
from .platform import assert_supported
from .render import render_vertical_clip
from .transcribe import DEFAULT_MODEL, transcribe_video

Progress = Callable[[str, float], None]


def run(
    source: str,
    workspace: Path,
    max_clips: int = 5,
    ollama_model: str = "qwen3:4b",
    whisper_model: str = DEFAULT_MODEL,
    language: str | None = None,
    progress: Progress | None = None,
) -> Path:
    caps = assert_supported()
    emit = progress or (lambda _message, _value: None)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = workspace.expanduser().resolve() / run_id
    download_dir = run_dir / "source"
    clips_dir = run_dir / "clips"
    run_dir.mkdir(parents=True, exist_ok=True)

    emit("Quelle laden", 0.05)
    video = resolve_source(source, download_dir)

    emit("Mit MLX Whisper transkribieren", 0.20)
    transcript, segments = transcribe_video(video, model=whisper_model, language=language)
    if not segments:
        raise RuntimeError("Whisper found no usable speech segments.")

    emit("Highlights lokal mit Ollama auswählen", 0.50)
    highlights = select_highlights(segments, max_clips=max_clips, model=ollama_model)

    outputs = []
    total = max(1, len(highlights))
    for idx, clip in enumerate(highlights, start=1):
        emit(f"Clip {idx}/{len(highlights)} rendern", 0.60 + 0.35 * ((idx - 1) / total))
        output = clips_dir / f"short_{idx:02d}.mp4"
        render_vertical_clip(
            video,
            output,
            float(clip["start"]),
            float(clip["end"]),
            prefer_videotoolbox=caps.videotoolbox,
        )
        outputs.append({
            **clip,
            "file": str(output.relative_to(run_dir)),
        })

    metadata = {
        "source_input": source,
        "source_file": str(video),
        "whisper_model": whisper_model,
        "ollama_model": ollama_model,
        "transcript": transcript,
        "clips": outputs,
    }
    (run_dir / "run.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    emit("Fertig", 1.0)
    return run_dir
