#!/usr/bin/env python3
"""
Test the design agent directly (no API): planner → API designer → Zapier tool selection.

Runs the agent to check that it:
  - plans right (services, task_description, valid)
  - sets correct endpoints (method, path, summary)
  - extracts related Zapier tools (selected by LLM)

Prerequisites:
  Copy .env.example to .env and set ANTHROPIC_API_KEY, ZAPIER_MCP_SERVER_URL, ZAPIER_MCP_SECRET.

Run from project root:
  python scripts/test_agent_api.py
  python scripts/test_agent_api.py --prompt "Your task here."
"""

from __future__ import annotations

import argparse
import json
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
        description="Test the design agent (planner → API designer → Zapier tool selection)"
    )
    parser.add_argument(
        "--prompt",
        default="Analyze cards in a Trello board and create events in Google Calendar for each card.",
        help="Task prompt for the design agent",
    )
    args = parser.parse_args()

    from core.agent import run_design_agent

    print("Running design agent (planner → API designer → Zapier tool selection)...")
    print("Prompt:", args.prompt[:80] + ("..." if len(args.prompt) > 80 else ""))
    print("-" * 60)

    try:
        state = run_design_agent(args.prompt)
    except Exception as e:
        print("Agent failed:", e)
        sys.exit(1)

    # Planner context
    planner = state.get("planner_context") or {}
    print("\n--- Planner ---")
    print("valid:", planner.get("valid"))
    if not planner.get("valid"):
        print("validation_reason:", planner.get("validation_reason"))
    print("services:", planner.get("services"))
    print("task_description (first 300 chars):", (planner.get("task_description") or "")[:300])

    # API design (endpoints)
    api_design = planner.get("api_design") or {}
    endpoints = api_design.get("endpoints") or []
    print("\n--- API design (endpoints) ---")
    for i, ep in enumerate(endpoints):
        print(f"  {i + 1}. {ep.get('method')} {ep.get('path')} — {ep.get('summary')}")

    # Available Zapier tools (what the agent saw before LLM selection)
    available = state.get("available_zapier_tools") or []
    print("\n--- Available Zapier tools (before selection) ---")
    print("count:", len(available))
    for t in available:
        name = getattr(t, "name", None) or ""
        desc = (getattr(t, "description", None) or "")[:55]
        if len(getattr(t, "description", None) or "") > 55:
            desc += "..."
        print(f"  - {name}: {desc}")

    # Selected Zapier tools
    selected = state.get("selected_zapier_tools") or []
    print("\n--- Selected Zapier tools ---")
    print("count:", len(selected))
    for t in selected:
        desc = (t.get("description") or "")[:60]
        if len(t.get("description") or "") > 60:
            desc += "..."
        print(f"  - {t.get('name')}: {desc}")

    # Context for coding agent (summary)
    ctx = state.get("context_for_coding_agent") or {}
    print("\n--- Context for coding agent ---")
    print("keys:", list(ctx.keys()))

    print("\nDone.")


if __name__ == "__main__":
    main()
