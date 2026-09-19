# LocalShorts Mac MVP

A local-first short-video pipeline for Apple Silicon.

This branch intentionally does **not** replace the existing web/SaaS app. The Mac implementation lives under `local-mac/` so it can be developed and tested independently.

## MVP flow

```
YouTube URL / local video
        ↓
      yt-dlp
        ↓
 MLX Whisper on Apple Silicon
        ↓
 timestamped transcript
        ↓
 Ollama (local LLM)
        ↓
 block-wise highlight selection
        ↓
 FFmpeg 9:16 crop
        ↓
 h264_videotoolbox
        ↓
 local MP4 shorts
```

The highlight stage analyses the transcript in ~5 minute blocks instead of sending only the first fixed number of Whisper segments to the LLM. This keeps long podcasts and interviews eligible across their full duration.

## Requirements

- Apple Silicon Mac (M1 or newer)
- macOS 13+
- Homebrew
- Ollama
- FFmpeg
- Python 3.12
- Rust + Node.js only for building the desktop shell

## 1. Bootstrap

```bash
cd local-mac
chmod +x scripts/*.sh
./scripts/bootstrap_mac.sh
```

The script installs/checks FFmpeg, Ollama and Python 3.12, creates `.venv`, installs the Python package and pulls `qwen3:4b` when necessary.

## 2. Test the pipeline from Terminal

```bash
source .venv/bin/activate
localshorts "https://www.youtube.com/watch?v=VIDEO_ID" --clips 3
```

For a local file:

```bash
localshorts "/Users/me/Movies/source.mp4" --clips 5
```

Output goes to:

```
~/Movies/LocalShorts/<timestamp>/
├── source/
├── clips/
│   ├── short_01.mp4
│   └── ...
└── run.json
```

## 3. Build the native Tauri sidecar

Install Rust if needed:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Then:

```bash
cd local-mac
source .venv/bin/activate
./scripts/build_sidecar.sh
```

This uses PyInstaller and writes the architecture-suffixed sidecar expected by Tauri, for example:

```
desktop/src-tauri/binaries/localshorts-sidecar-aarch64-apple-darwin
```

## 4. Run the desktop app

```bash
cd desktop
npm install
npm run dev
```

The Tauri window starts the bundled Python sidecar on `127.0.0.1:17891`. Video processing remains local. Network access is only needed for downloading a URL, downloading model weights the first time, and any platform publishing added later.

## 5. Build a DMG

```bash
cd local-mac
source .venv/bin/activate
./scripts/build_sidecar.sh

cd desktop
npm install
npm run build
```

The DMG will be created by Tauri under its normal `src-tauri/target/.../bundle/dmg/` output tree.

## Current MVP limitations

- The first renderer uses a robust center 9:16 crop. Dynamic face/person follow-crop is the next pipeline milestone.
- Captions are not burned into the first Mac branch yet.
- The UI currently accepts a local **path**. Native Finder file-picking is the next desktop integration.
- The app expects Ollama to be installed/running. A later release can replace this dependency with an embedded MLX/llama.cpp model runtime.
- The DMG is not yet Developer-ID signed or notarized.

## Planned next milestones

1. Native Finder video picker.
2. MLX/Apple Vision subject tracking and dynamic 9:16 reframing.
3. Styled captions with safe-area templates.
4. SQLite project/job persistence.
5. Clip preview trim editor.
6. App settings/model manager.
7. Signed + notarized universal distribution workflow.
