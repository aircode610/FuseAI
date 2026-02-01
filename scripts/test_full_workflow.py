#!/usr/bin/env python3
"""
Test the full workflow: design agent → code generator.

Runs:
  1. Design agent (planner → API designer → Zapier tool selection with LLM).
  2. Code generator (LLM generates main.py from template + context).

Prerequisites:
  .env with ANTHROPIC_API_KEY, ZAPIER_MCP_SERVER_URL, ZAPIER_MCP_SECRET.

Run from project root:
  python scripts/test_full_workflow.py
  python scripts/test_full_workflow.py --prompt "Your task here."
  python scripts/test_full_workflow.py --agent-id my_agent
"""

from __future__ import annotations

import argparse
import sys
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test full workflow: design agent → code generator"
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
    args = parser.parse_args()

    from core.agent import run_design_agent
    from core.code_generator import generate_agent

    print("=" * 60)
    print("Full workflow: design agent → code generator")
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

    print(f"  Wrote: {main_py}")
    print(f"  Size:  {main_py.stat().st_size} bytes")

    print("\n" + "=" * 60)
    print("Done. Full workflow completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
