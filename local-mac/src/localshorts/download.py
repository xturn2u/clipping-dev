from __future__ import annotations

import os
from pathlib import Path

import yt_dlp


def resolve_source(source: str, download_dir: Path) -> Path:
    source = source.strip()
    if os.path.isfile(source):
        return Path(source).expanduser().resolve()

    if not source.startswith(("http://", "https://")):
        raise ValueError("Source must be a local video file or http(s) URL.")

    download_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "format": "bv*+ba/b",
        "outtmpl": str(download_dir / "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(source, download=True)
        requested = (info or {}).get("requested_downloads") or []
        for item in requested:
            filepath = item.get("filepath")
            if filepath and Path(filepath).is_file():
                return Path(filepath).resolve()

        video_id = (info or {}).get("id")
        if video_id:
            candidates = sorted(download_dir.glob(f"{video_id}*"), key=lambda p: p.stat().st_mtime, reverse=True)
            for candidate in candidates:
                if candidate.is_file() and candidate.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}:
                    return candidate.resolve()

    raise FileNotFoundError("yt-dlp completed but no downloaded video file was found.")
