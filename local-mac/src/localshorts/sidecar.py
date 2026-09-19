from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .pipeline import run
from .transcribe import DEFAULT_MODEL

HOST = "127.0.0.1"
PORT = 17891


class JobRequest(BaseModel):
    source: str
    clips: int = Field(default=5, ge=1, le=10)
    ollama_model: str = "qwen3:4b"
    whisper_model: str = DEFAULT_MODEL
    language: str | None = None


@dataclass
class Job:
    id: str
    status: str = "queued"
    message: str = "Wartet"
    progress: float = 0.0
    error: str | None = None
    run_dir: Path | None = None
    clips: list[str] = field(default_factory=list)


JOBS: dict[str, Job] = {}
LOCK = threading.Lock()
WORKSPACE = Path.home() / "Movies" / "LocalShorts"


app = FastAPI(title="LocalShorts Mac Sidecar", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _snapshot(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "status": job.status,
        "message": job.message,
        "progress": job.progress,
        "error": job.error,
        "clips": job.clips,
    }


def _worker(job: Job, req: JobRequest) -> None:
    with LOCK:
        job.status = "running"
        job.message = "Startet"

    def on_progress(message: str, value: float) -> None:
        with LOCK:
            job.message = message
            job.progress = max(0.0, min(1.0, value))

    try:
        run_dir = run(
            source=req.source,
            workspace=WORKSPACE,
            max_clips=req.clips,
            ollama_model=req.ollama_model,
            whisper_model=req.whisper_model,
            language=req.language,
            progress=on_progress,
        )
        clip_files = sorted((run_dir / "clips").glob("*.mp4"))
        with LOCK:
            job.run_dir = run_dir
            job.clips = [p.name for p in clip_files]
            job.status = "done"
            job.message = f"{len(clip_files)} Clip(s) fertig"
            job.progress = 1.0
    except Exception as exc:
        with LOCK:
            job.status = "failed"
            job.error = str(exc)
            job.message = "Fehler"
            job.progress = 1.0


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "version": app.version}


@app.post("/api/jobs")
def create_job(req: JobRequest) -> dict[str, Any]:
    job = Job(id=uuid.uuid4().hex[:12])
    with LOCK:
        JOBS[job.id] = job
    threading.Thread(target=_worker, args=(job, req), daemon=True).start()
    return _snapshot(job)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    with LOCK:
        job = JOBS.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return _snapshot(job)


@app.get("/api/jobs/{job_id}/clips/{filename}")
def get_clip(job_id: str, filename: str) -> FileResponse:
    with LOCK:
        job = JOBS.get(job_id)
        run_dir = job.run_dir if job else None
    if run_dir is None:
        raise HTTPException(status_code=404, detail="Run not ready")
    safe_name = Path(filename).name
    path = run_dir / "clips" / safe_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(path, media_type="video/mp4", filename=safe_name)


def main() -> None:
    # Finder-launched macOS apps often do not inherit the interactive shell PATH.
    # Make the standard Apple Silicon Homebrew location visible to FFmpeg checks.
    current_path = os.environ.get("PATH", "")
    extra = ["/opt/homebrew/bin", "/usr/local/bin"]
    os.environ["PATH"] = ":".join(extra + [current_path])
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
