#!/usr/bin/env python3
"""
Test the full workflow: design agent → code generator → deployer (server + HTTP tests).

Runs:
  1. Design agent (planner → API designer → Zapier tool selection).
  2. Code generator (LLM generates main.py from template + context).
  3. Start server via core.deployer.deploy_agent in a subprocess.
  4. Wait for server ready, then GET /health and optional POST to first endpoint.
  5. Stop the server.

Prerequisites:
  .env with ANTHROPIC_API_KEY, ZAPIER_MCP_SERVER_URL, ZAPIER_MCP_SECRET.

Run from project root:
  python scripts/test_full_workflow.py
  python scripts/test_full_workflow.py --prompt "Your task here."
  python scripts/test_full_workflow.py --agent-id my_agent --port 8001
  python scripts/test_full_workflow.py --no-deploy   # skip starting server and HTTP tests
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Allow running from project root without installing
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except ImportError:
    pass


def _wait_for_server(port: int, timeout_sec: float = 30) -> bool:
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.5)
    return False


def _http_get(port: int, path: str) -> tuple[int, str]:
    url = f"http://127.0.0.1:{port}{path}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return (resp.status, body)
    except urllib.error.HTTPError as e:
        return (e.code, e.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return (0, str(e))


def _http_post(port: int, path: str, query: str = "", body: bytes | None = None) -> tuple[int, str]:
    url = f"http://127.0.0.1:{port}{path}"
    if query:
        url += "?" + query
    try:
        req = urllib.request.Request(url, data=body or b"", method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = resp.read().decode("utf-8", errors="replace")
            return (resp.status, out)
    except urllib.error.HTTPError as e:
        return (e.code, e.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return (0, str(e))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test full workflow: design agent → code generator → deployer (server + HTTP tests)"
    )
    parser.add_argument(
        "--prompt",
        default="summarize the last n emails in my gmail if there is anyone needing a meeting schedule one in my google calendar",
        help="Task prompt for the design agent",
    )
    parser.add_argument(
        "--agent-id",
        default=None,
        help="Agent ID for output dir (default: agent_<timestamp>)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for the deployed agent server (default 8001)",
    )
    parser.add_argument(
        "--no-deploy",
        action="store_true",
        help="Skip starting server and HTTP tests (only run design agent + code generator)",
    )
    args = parser.parse_args()

    from core.agent import run_design_agent
    from core.code_generator import generate_agent

    print("=" * 60)
    print("Full workflow: design agent → code generator → deployer")
    print("=" * 60)
    print("\nPrompt:", args.prompt[:80] + ("..." if len(args.prompt) > 80 else ""))

    print("\n--- Step 1: Design agent (planner → API designer → Zapier tool selection) ---")
    try:
        state = run_design_agent(args.prompt)
    except Exception as e:
        print("Design agent failed:", e)
        sys.exit(1)

    context = state.get("context_for_coding_agent")
    if not context:
        print("No context_for_coding_agent in state.")
        sys.exit(1)

    api_design = context.get("api_design") or {}
    endpoints = api_design.get("endpoints") or []
    selected = context.get("selected_zapier_tools") or []
    print(f"  Endpoints: {len(endpoints)}")
    for ep in endpoints:
        print(f"    - {ep.get('method')} {ep.get('path')} — {ep.get('summary', '')[:50]}")
    print(f"  Selected Zapier tools: {len(selected)}")
    for t in selected[:5]:
        print(f"    - {t.get('name')}")
    if len(selected) > 5:
        print(f"    ... and {len(selected) - 5} more")

    print("\n--- Step 2: Code generator (LLM generates main.py from template + context) ---")
    try:
        main_py = generate_agent(
            context_for_coding_agent=context,
            agent_id=args.agent_id,
        )
    except Exception as e:
        print("Code generator failed:", e)
        sys.exit(1)

    if not main_py.exists():
        print("Generated file not found:", main_py)
        sys.exit(1)

    agent_id = main_py.parent.name
    print(f"  Wrote: {main_py}")
    print(f"  Agent ID: {agent_id}")
    print(f"  Size:  {main_py.stat().st_size} bytes")

    if args.no_deploy:
        print("\n" + "=" * 60)
        print("Done. (Skipped deploy and HTTP tests; use --port and run without --no-deploy to test server.)")
        print("=" * 60)
        return

    print("\n--- Step 3: Start server via core.deployer.deploy_agent ---")
    env = os.environ.copy()
    env["FUSEAI_AGENT_ID"] = agent_id
    env["FUSEAI_PORT"] = str(args.port)
    _root_str = str(_root.resolve())
    env["FUSEAI_ROOT"] = _root_str
    cmd = [
        sys.executable, "-c",
        "import os, sys; "
        "sys.path.insert(0, os.environ['FUSEAI_ROOT']); "
        "from pathlib import Path; "
        "from core.deployer import deploy_agent; "
        "root = Path(os.environ['FUSEAI_ROOT']).resolve(); "
        "deploy_agent(agent_id=os.environ['FUSEAI_AGENT_ID'], port=int(os.environ['FUSEAI_PORT']), project_root=root)",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(_root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        print(f"  Server starting on http://127.0.0.1:{args.port} (PID {proc.pid})")
        if not _wait_for_server(args.port):
            stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
            print("  Server did not become ready in time.")
            if stderr:
                print("  stderr:", stderr[:500])
            proc.terminate()
            proc.wait(timeout=5)
            sys.exit(1)
        print("  Server is ready.")

        print("\n--- Step 4: HTTP tests ---")
        status, body = _http_get(args.port, "/health")
        print(f"  GET /health -> {status}")
        if status != 200:
            print(f"    Body: {body[:200]}")
        else:
            print(f"    Body: {body.strip()[:100]}")

        if endpoints:
            ep = endpoints[0]
            path = ep.get("path") or "/execute"
            method = (ep.get("method") or "POST").upper()
            if method == "GET":
                status, body = _http_get(args.port, path)
            else:
                query_parts = []
                for q in ep.get("query_parameters") or []:
                    name = q.get("name") or "n"
                    query_parts.append(f"{name}=1")
                query = "&".join(query_parts) if query_parts else ""
                status, body = _http_post(args.port, path, query=query, body=b"{}")
            print(f"  {method} {path} -> {status}")
            if len(body) > 300:
                body = body[:300] + "..."
            print(f"    Body: {body}")
    finally:
        print("\n--- Step 5: Stop server ---")
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print("  Server stopped.")

    print("\n" + "=" * 60)
    print("Done. Full workflow completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
