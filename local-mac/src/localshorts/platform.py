from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class MacCapabilities:
    is_macos: bool
    is_apple_silicon: bool
    ffmpeg: str | None
    ffprobe: str | None
    videotoolbox: bool


def detect_capabilities() -> MacCapabilities:
    is_macos = platform.system() == "Darwin"
    is_apple_silicon = is_macos and platform.machine().lower() in {"arm64", "aarch64"}
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    return MacCapabilities(
        is_macos=is_macos,
        is_apple_silicon=is_apple_silicon,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        videotoolbox=is_apple_silicon and ffmpeg is not None,
    )


def assert_supported() -> MacCapabilities:
    caps = detect_capabilities()
    if not caps.is_macos:
        raise RuntimeError("This MVP is intentionally macOS-first.")
    if not caps.is_apple_silicon:
        raise RuntimeError("This MVP currently requires an Apple Silicon Mac (M1 or newer).")
    if not caps.ffmpeg or not caps.ffprobe:
        raise RuntimeError("FFmpeg/FFprobe not found. Install with: brew install ffmpeg")
    return caps
