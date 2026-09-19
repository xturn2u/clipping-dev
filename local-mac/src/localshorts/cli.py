from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run
from .transcribe import DEFAULT_MODEL


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate local vertical shorts on Apple Silicon.")
    parser.add_argument("source", help="YouTube/video URL or local video file")
    parser.add_argument("--clips", type=int, default=5, choices=range(1, 11))
    parser.add_argument("--ollama-model", default="qwen3:4b")
    parser.add_argument("--whisper-model", default=DEFAULT_MODEL)
    parser.add_argument("--language", default=None)
    parser.add_argument("--workspace", type=Path, default=Path.home() / "Movies" / "LocalShorts")
    args = parser.parse_args()

    def show(message: str, value: float) -> None:
        print(f"[{value:>5.0%}] {message}", flush=True)

    run_dir = run(
        source=args.source,
        workspace=args.workspace,
        max_clips=args.clips,
        ollama_model=args.ollama_model,
        whisper_model=args.whisper_model,
        language=args.language,
        progress=show,
    )
    print(f"\nDone: {run_dir}")


if __name__ == "__main__":
    main()
