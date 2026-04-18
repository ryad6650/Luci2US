"""Persist the latest SWEX profile payload on disk so the Profile page can
survive a restart without needing a fresh SWEX drop."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_PATH = "profile_cache.json"


def _wrap(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }


def save_profile_payload(payload: dict[str, Any], path: str | Path = DEFAULT_PATH) -> None:
    """Atomically overwrite the cache file with the raw SWEX payload."""
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_wrap(payload), f, ensure_ascii=False)
    os.replace(tmp, p)


def load_profile_payload(path: str | Path = DEFAULT_PATH) -> tuple[dict[str, Any], str] | None:
    """Return (payload, saved_at) or None if no cache on disk."""
    p = Path(path)
    if not p.is_file():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    payload = data.get("payload")
    saved_at = data.get("saved_at", "")
    if not isinstance(payload, dict):
        return None
    return payload, saved_at
