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


DEFAULT_PROMPT = """Create an API that collects feedback from a Slack channel's messages 
from the last week, analyzes sentiment and themes, creates a summary 
document in Google Docs with categorized feedback, and creates Trello 
cards for each action item
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
