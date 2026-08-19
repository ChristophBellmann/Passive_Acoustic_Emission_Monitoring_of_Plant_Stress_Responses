"""Utility functions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def ensure_output_dirs(base: Path) -> dict[str, Path]:
    raw = base / "data" / "raw"
    processed = base / "data" / "processed"
    reports = base / "data" / "reports"
    for d in [raw, processed, reports]:
        d.mkdir(parents=True, exist_ok=True)
    return {"raw": raw, "processed": processed, "reports": reports}


def timestamp_str() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
