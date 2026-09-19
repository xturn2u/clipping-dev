#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "This MVP requires macOS on Apple Silicon."
  exit 1
fi

command -v brew >/dev/null 2>&1 || {
  echo "Homebrew is required: https://brew.sh"
  exit 1
}

brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
brew list ollama >/dev/null 2>&1 || brew install ollama
brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12

PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

if ! ollama list >/dev/null 2>&1; then
  echo "Start Ollama once, then rerun this script."
  exit 1
fi

if ! ollama list | grep -q "qwen3:4b"; then
  ollama pull qwen3:4b
fi

echo
echo "LocalShorts Mac is ready."
echo "CLI example:"
echo "  source .venv/bin/activate"
echo "  localshorts 'https://www.youtube.com/watch?v=...' --clips 3"
