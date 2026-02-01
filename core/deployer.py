"""
Deploy a generated agent by agent_id: load tools (if manifest exists), build app, run uvicorn.

Same logic as scripts/run_deployed_agent.py — use this from API or scripts to run
a deployed agent. Takes agent_id as input and starts the FastAPI app (blocking).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Project root (parent of core/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEPLOYED_AGENTS_DIR = _PROJECT_ROOT / "runtime" / "deployed_agents"


def get_agent_dir(agent_id: str, project_root: Path | None = None) -> Path:
    """Return the directory for a deployed agent (runtime/deployed_agents/<agent_id>)."""
    root = project_root or _PROJECT_ROOT
    return root / "runtime" / "deployed_agents" / agent_id


async def load_tools_for_agent(agent_dir: Path) -> list[Any] | None:
    """
    Load Zapier tools using tools_manifest.json; return list of LangChain tools.

    Returns None if no manifest (legacy agent). Returns [] if manifest exists but no tools.
    """
    manifest_path = agent_dir / "tools_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tool_names = list(manifest.get("tool_names") or [])
    services = list(manifest.get("services") or [])
    if not tool_names:
        return []
    from core.zapier_mapper import get_zapier_tools
    all_tools = await get_zapier_tools(services=services if services else None)
    names_set = {n.strip().lower() for n in tool_names if n}
    return [t for t in all_tools if (getattr(t, "name", None) or "").strip().lower() in names_set]


def _create_app_with_tools(agent_dir: Path, tools: list[Any], project_root: Path) -> Any:
    """Import agent main and call create_app(tools); return FastAPI app."""
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(agent_dir))
    try:
        import main as agent_main  # noqa: PLC0415
    finally:
        sys.path.remove(str(agent_dir))
    if not hasattr(agent_main, "create_app"):
        raise AttributeError("Agent main.py has no create_app(tools)")
    return agent_main.create_app(tools)


def deploy_agent(
    agent_id: str,
    port: int = 8001,
    host: str = "0.0.0.0",
    project_root: Path | None = None,
    use_reload: bool = False,
) -> None:
    """
    Deploy (run) a generated agent by agent_id. Blocking — runs uvicorn until shutdown.

    Same behavior as scripts/run_deployed_agent.py:
    - If tools_manifest.json exists and agent has create_app(tools): load tools, create_app(tools), uvicorn.run(app).
    - Else: subprocess uvicorn main:app --app-dir <agent_dir> (legacy).

    Raises FileNotFoundError if agent_dir/main.py does not exist.
    """
    root = project_root or _PROJECT_ROOT
    agent_dir = get_agent_dir(agent_id, project_root=root)
    main_py = agent_dir / "main.py"

    if not main_py.exists():
        raise FileNotFoundError(
            f"Agent not found: {main_py}. List deployed agents: ls runtime/deployed_agents/"
        )

    tools = asyncio.run(load_tools_for_agent(agent_dir))

    if tools is not None:
        try:
            app = _create_app_with_tools(agent_dir, tools, root)
        except AttributeError:
            tools = None
        else:
            import uvicorn
            uvicorn.run(app, host=host, port=port)
            return

    # Legacy: agent loads tools itself via get_zapier_tools
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--app-dir",
        str(agent_dir),
        "--host",
        host,
        "--port",
        str(port),
    ]
    if use_reload:
        cmd.append("--reload")
    subprocess.run(cmd, cwd=str(root), env=os.environ.copy())
