"""
Per-agent metrics: record API call status and duration, read aggregates.
Stored under runtime/metrics/{agent_id}.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_METRICS_DIR = _PROJECT_ROOT / "runtime" / "metrics"


def _metrics_path(agent_id: str) -> Path:
    _METRICS_DIR.mkdir(parents=True, exist_ok=True)
    return _METRICS_DIR / f"{agent_id}.json"


def _load_metrics(agent_id: str) -> dict[str, Any]:
    path = _metrics_path(agent_id)
    if not path.exists():
        return {"calls": [], "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("calls", [])
        return data
    except Exception:
        return {"calls": [], "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def _save_metrics(agent_id: str, data: dict[str, Any]) -> None:
    path = _metrics_path(agent_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_call(agent_id: str, status: int, duration_ms: int, path: str = "") -> None:
    """Record one API call (from test endpoint proxy)."""
    data = _load_metrics(agent_id)
    success = 200 <= status < 400
    data["calls"].append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status,
        "duration_ms": duration_ms,
        "success": success,
        "path": path or "/",
    })
    # Keep last N calls to avoid huge files (e.g. 1000)
    max_calls = 1000
    if len(data["calls"]) > max_calls:
        data["calls"] = data["calls"][-max_calls:]
    _save_metrics(agent_id, data)


def get_metrics(agent_id: str, time_range: str = "all") -> dict[str, Any]:
    """Return aggregated metrics for the agent (totalRequests, successRate, etc.)."""
    data = _load_metrics(agent_id)
    calls = data.get("calls") or []

    # Optional: filter by time_range (e.g. 24h, 7d) - for now return all
    # Could filter by timestamp if needed

    total = len(calls)
    successful = sum(1 for c in calls if c.get("success", False))
    failed = total - successful
    success_rate = (successful / total) if total else 0.0
    durations = [c.get("duration_ms", 0) for c in calls if isinstance(c.get("duration_ms"), (int, float))]
    avg_ms = int(sum(durations) / len(durations)) if durations else 0
    min_ms = min(durations) if durations else 0
    max_ms = max(durations) if durations else 0
    sorted_durations = sorted(durations) if durations else []
    p95_idx = int(len(sorted_durations) * 0.95) - 1
    p95_ms = sorted_durations[p95_idx] if p95_idx >= 0 and sorted_durations else 0

    # Requests over time (by day) - last 7 days
    by_day: dict[str, int] = {}
    for c in calls:
        ts = c.get("timestamp", "")[:10]  # YYYY-MM-DD
        if ts:
            by_day[ts] = by_day.get(ts, 0) + 1
    days_order = sorted(by_day.keys(), reverse=True)[:7]
    requests_over_time = [{"day": d, "value": by_day[d]} for d in reversed(days_order)]

    return {
        "totalRequests": total,
        "successful": successful,
        "failed": failed,
        "successRate": round(success_rate, 4),
        "avgResponseTime": avg_ms,
        "minResponseTime": min_ms,
        "maxResponseTime": max_ms,
        "p95ResponseTime": p95_ms,
        "requestsOverTime": requests_over_time,
        "calls": calls[-100:],  # Last 100 raw calls for charts if needed
    }


def delete_agent_metrics(agent_id: str) -> bool:
    """Remove metrics file for an agent. Returns True if deleted."""
    path = _metrics_path(agent_id)
    if path.exists():
        path.unlink()
        return True
    return False
