#!/usr/bin/env python3
"""
Test planner -> API designer pipeline: run planner, then api_designer, print design.

Usage:
  python scripts/test_api_designer.py
  python scripts/test_api_designer.py "Your custom prompt here"

Requires .env with ANTHROPIC_API_KEY for planner. API designer is deterministic (no LLM).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.planner import run_planner
from core.api_designer import run_api_designer


DEFAULT_PROMPT = """
Create an API that:

1. Analyzes our current sprint - get all Trello cards for this sprint, 
   check their progress, calculate velocity, identify risks (overdue cards, 
   blocked items, unassigned work), and post a health report to Slack

2. Take corrective action - when we're behind, automatically reassign cards 
   from overloaded team members to available ones, update due dates to be 
   realistic, and notify affected people in Slack

"""


def main() -> None:
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    print("Running planner + API designer with prompt:")
    print(f"  {prompt!r}\n")

    planner_state = run_planner(prompt)
    if planner_state.get("errors"):
        print("Planner errors:", planner_state["errors"])
    design = run_api_designer(planner_state)

    print("--- API Design (code-gen ready, %d endpoint(s)) ---" % len(design.endpoints))
    print(design.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
