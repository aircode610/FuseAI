"""
Per-agent logs: append log entries (errors from failed API calls, optional info).
Stored under runtime/logs/{agent_id}.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOGS_DIR = _PROJECT_ROOT / "runtime" / "logs"


def _logs_path(agent_id: str) -> Path:
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return _LOGS_DIR / f"{agent_id}.json"


def _load_logs(agent_id: str) -> list[dict[str, Any]]:
    path = _logs_path(agent_id)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_logs(agent_id: str, entries: list[dict[str, Any]]) -> None:
    path = _logs_path(agent_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep last 500 entries
    if len(entries) > 500:
        entries = entries[-500:]
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def log_error(agent_id: str, message: str, details: dict[str, Any] | None = None) -> None:
    """Append an error log entry (e.g. when an API request fails)."""
    entries = _load_logs(agent_id)
    entries.append({
        "id": len(entries) + 1,
        "level": "error",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "message": message,
        "details": details or {},
    })
    _save_logs(agent_id, entries)


def log_info(agent_id: str, message: str, details: dict[str, Any] | None = None) -> None:
    """Append an info log entry (e.g. successful request)."""
    entries = _load_logs(agent_id)
    entries.append({
        "id": len(entries) + 1,
        "level": "info",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "message": message,
        "details": details or {},
    })
    _save_logs(agent_id, entries)


def get_logs(agent_id: str, level: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return log entries for the agent, optionally filtered by level."""
    entries = _load_logs(agent_id)
    if level and level != "all":
        entries = [e for e in entries if e.get("level") == level]
    return list(reversed(entries[-limit:]))  # Newest first


def delete_agent_logs(agent_id: str) -> bool:
    """Remove logs file for an agent. Returns True if deleted."""
    path = _logs_path(agent_id)
    if path.exists():
        path.unlink()
        return True
    return False
