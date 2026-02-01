#!/usr/bin/env python3
"""
Run and test a deployed agent's main.py.

If the agent has tools_manifest.json (new flow), loads Zapier tools and passes them
to create_app(tools). Otherwise runs uvicorn main:app (legacy agents that call get_zapier_tools themselves).

Prerequisites:
  Run from project root. .env must have ANTHROPIC_API_KEY, ZAPIER_MCP_SERVER_URL, ZAPIER_MCP_SECRET.

Usage:
  python scripts/run_deployed_agent.py <agent_id>
  python scripts/run_deployed_agent.py agent_1769910594 --port 8001

Then test:
  curl http://localhost:8001/health
  curl -X POST "http://localhost:8001/analyze-cards-create-events/YOUR_BOARD_ID"
  Open http://localhost:8001/docs for Swagger UI
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Project root
_ROOT = Path(__file__).resolve().parent.parent

# Load .env so Zapier MCP and Anthropic are available
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


async def _load_tools_for_agent(agent_dir: Path):
    """Load Zapier tools using tools_manifest.json; return list of LangChain tools."""
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a deployed agent's main.py (FastAPI app)"
    )
    parser.add_argument(
        "agent_id",
        help="Agent ID (e.g. agent_1769910594) — directory under runtime/deployed_agents/",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for the agent (default 8001, so it doesn't clash with main API on 8000)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable reload (use for production-like run)",
    )
    args = parser.parse_args()

    agent_dir = _ROOT / "runtime" / "deployed_agents" / args.agent_id
    main_py = agent_dir / "main.py"

    if not main_py.exists():
        print(f"Agent not found: {main_py}")
        print("List deployed agents: ls runtime/deployed_agents/")
        sys.exit(1)

    tools = asyncio.run(_load_tools_for_agent(agent_dir))

    if tools is not None:
        # New flow: pass LangChain tools to create_app(tools)
        sys.path.insert(0, str(agent_dir))
        try:
            import main as agent_main
        except ImportError as e:
            print(f"Failed to import agent main: {e}")
            sys.exit(1)
        if not hasattr(agent_main, "create_app"):
            print("Agent main.py has no create_app(tools); falling back to main:app.")
            sys.path.remove(str(agent_dir))
            tools = None
        else:
            app = agent_main.create_app(tools)
            sys.path.remove(str(agent_dir))
            print(f"Running agent: {args.agent_id} (tools passed to create_app: {len(tools)} tools)")
            print(f"  App dir: {agent_dir}")
            print(f"  Port:    http://localhost:{args.port}")
            print(f"  Health:  curl http://localhost:{args.port}/health")
            print(f"  Docs:    http://localhost:{args.port}/docs")
            print("-" * 50)
            import uvicorn
            # reload not supported when passing app object; use legacy main:app for --reload
            uvicorn.run(app, host="0.0.0.0", port=args.port)
            return

    # Legacy flow: uvicorn main:app (agent loads tools itself via get_zapier_tools)
    import subprocess
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--app-dir",
        str(agent_dir),
        "--host",
        "0.0.0.0",
        "--port",
        str(args.port),
    ]
    if not args.no_reload:
        cmd.append("--reload")
    print(f"Running agent: {args.agent_id} (legacy main:app)")
    print(f"  App dir: {agent_dir}")
    print(f"  Port:    http://localhost:{args.port}")
    print(f"  Health:  curl http://localhost:{args.port}/health")
    print("-" * 50)
    subprocess.run(cmd, cwd=str(_ROOT), env=os.environ.copy())


if __name__ == "__main__":
    main()
