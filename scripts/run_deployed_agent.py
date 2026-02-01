#!/usr/bin/env python3
"""
Run and test a deployed agent's main.py.

Uses core.deployer.deploy_agent: loads Zapier tools from tools_manifest.json (if present),
passes them to create_app(tools), or falls back to uvicorn main:app for legacy agents.

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
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass


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
        help="Disable reload (use for production-like run; only applies to legacy main:app)",
    )
    args = parser.parse_args()

    from core.deployer import deploy_agent, get_agent_dir

    agent_dir = get_agent_dir(args.agent_id, project_root=_ROOT)
    if not (agent_dir / "main.py").exists():
        print(f"Agent not found: {agent_dir / 'main.py'}")
        print("List deployed agents: ls runtime/deployed_agents/")
        sys.exit(1)

    print(f"Running agent: {args.agent_id}")
    print(f"  App dir: {agent_dir}")
    print(f"  Port:    http://localhost:{args.port}")
    print(f"  Health:  curl http://localhost:{args.port}/health")
    print(f"  Docs:    http://localhost:{args.port}/docs")
    print("-" * 50)

    try:
        deploy_agent(
            agent_id=args.agent_id,
            port=args.port,
            project_root=_ROOT,
            use_reload=not args.no_reload,
        )
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
