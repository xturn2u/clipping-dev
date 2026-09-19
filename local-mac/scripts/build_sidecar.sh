#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate

python -m pip install -e ".[dev]"

rm -rf build dist
pyinstaller   --noconfirm   --clean   --onefile   --name localshorts-sidecar   --collect-all mlx_whisper   --collect-all mlx   --collect-submodules yt_dlp   --collect-submodules ollama   -m localshorts.sidecar

TARGET="$(rustc -Vv | awk '/host:/ {print $2}')"
DEST="$ROOT/desktop/src-tauri/binaries"
mkdir -p "$DEST"
cp "dist/localshorts-sidecar" "$DEST/localshorts-sidecar-$TARGET"
chmod +x "$DEST/localshorts-sidecar-$TARGET"

echo "Built Tauri sidecar: $DEST/localshorts-sidecar-$TARGET"
