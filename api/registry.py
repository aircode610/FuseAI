"""
Agent registry: load/save agent metadata to runtime/agents_registry.json.
Used by the backend API to list agents and return endpoint/parameter specs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _PROJECT_ROOT / "runtime" / "agents_registry.json"

DEFAULT_PORT_START = 8001


def _ensure_runtime_dir() -> Path:
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _REGISTRY_PATH.parent


def load_registry() -> dict[str, Any]:
    if not _REGISTRY_PATH.exists():
        return {"agents": [], "next_port": DEFAULT_PORT_START}
    try:
        data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        data.setdefault("agents", [])
        data.setdefault("next_port", DEFAULT_PORT_START)
        return data
    except Exception:
        return {"agents": [], "next_port": DEFAULT_PORT_START}


def save_registry(data: dict[str, Any]) -> None:
    _ensure_runtime_dir()
    _REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_agents() -> list[dict[str, Any]]:
    return list(load_registry().get("agents", []))


def get_agent(agent_id: str) -> dict[str, Any] | None:
    for a in list_agents():
        if a.get("id") == agent_id:
            return dict(a)
    return None


def add_agent(agent: dict[str, Any]) -> None:
    data = load_registry()
    agents = data["agents"]
    if any(a.get("id") == agent.get("id") for a in agents):
        return
    agents.append(agent)
    save_registry(data)


def update_agent(agent_id: str, updates: dict[str, Any]) -> bool:
    data = load_registry()
    for i, a in enumerate(data["agents"]):
        if a.get("id") == agent_id:
            data["agents"][i] = {**a, **updates}
            save_registry(data)
            return True
    return False


def remove_agent(agent_id: str) -> bool:
    data = load_registry()
    before = len(data["agents"])
    data["agents"] = [a for a in data["agents"] if a.get("id") != agent_id]
    if len(data["agents"]) < before:
        save_registry(data)
        return True
    return False


def reserve_port() -> int:
    data = load_registry()
    port = data.get("next_port", DEFAULT_PORT_START)
    data["next_port"] = port + 1
    save_registry(data)
    return port
