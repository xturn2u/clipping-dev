from __future__ import annotations

import json
from typing import Any

import ollama


def _content(response: Any) -> str:
    message = getattr(response, "message", None)
    if message is not None:
        return str(getattr(message, "content", "") or "")
    if isinstance(response, dict):
        msg = response.get("message") or {}
        return str(msg.get("content") or "")
    return ""


def _extract_json_array(text: str) -> list[dict]:
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _blocks(segments: list[dict], seconds: float = 300.0) -> list[list[tuple[int, dict]]]:
    if not segments:
        return []
    out: list[list[tuple[int, dict]]] = []
    current: list[tuple[int, dict]] = []
    block_start = float(segments[0]["start"])
    for idx, seg in enumerate(segments):
        if current and float(seg["start"]) - block_start >= seconds:
            out.append(current)
            current = []
            block_start = float(seg["start"])
        current.append((idx, seg))
    if current:
        out.append(current)
    return out


def _ask_block(block: list[tuple[int, dict]], model: str, min_duration: float, max_duration: float) -> list[dict]:
    lines = []
    for idx, seg in block:
        text = str(seg.get("text") or "").replace("\n", " ").strip()[:180]
        lines.append(f"[{idx}] {seg['start']:.1f}-{seg['end']:.1f}s {text}")

    prompt = f"""Select the strongest self-contained short-video moments from this transcript block.
Each candidate needs a hook and payoff and must be {min_duration:.0f}-{max_duration:.0f} seconds.
Return at most 4 candidates. Return JSON only:
[{{"start_idx": 10, "end_idx": 18, "score": 0-100, "reason": "short reason"}}]

Transcript:
{chr(10).join(lines)}
"""
    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    except Exception:
        return []
    return _extract_json_array(_content(response))


def select_highlights(
    segments: list[dict],
    max_clips: int = 5,
    model: str = "qwen3:4b",
    min_duration: float = 15.0,
    max_duration: float = 60.0,
) -> list[dict]:
    if not segments:
        return []

    candidates: list[dict] = []
    for block in _blocks(segments):
        for item in _ask_block(block, model, min_duration, max_duration):
            try:
                si = int(item["start_idx"])
                ei = int(item["end_idx"])
                score = float(item.get("score", 50))
            except (KeyError, TypeError, ValueError):
                continue
            if si < 0 or ei < si or ei >= len(segments):
                continue
            start = float(segments[si]["start"])
            end = float(segments[ei]["end"])
            duration = end - start
            if duration < min_duration or duration > max_duration + 5:
                continue
            candidates.append({
                "start": start,
                "end": min(end, start + max_duration),
                "score": max(0.0, min(100.0, score)),
                "reason": str(item.get("reason") or ""),
                "text": " ".join(str(s.get("text") or "") for s in segments[si : ei + 1]).strip(),
            })

    if not candidates:
        # Safe deterministic fallback so a temporary Ollama/model problem does not kill the run.
        video_end = float(segments[-1]["end"])
        start = 5.0
        while start + min_duration <= video_end and len(candidates) < max_clips:
            end = min(start + min(30.0, max_duration), video_end)
            candidates.append({"start": start, "end": end, "score": 1.0, "reason": "fallback", "text": ""})
            start = end + 10.0

    candidates.sort(key=lambda c: (-c["score"], c["start"]))
    selected: list[dict] = []
    for candidate in candidates:
        overlaps = any(candidate["start"] < s["end"] and candidate["end"] > s["start"] for s in selected)
        if overlaps:
            continue
        selected.append(candidate)
        if len(selected) >= max_clips:
            break

    selected.sort(key=lambda c: c["start"])
    return selected
