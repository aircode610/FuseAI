#!/usr/bin/env python3
"""
Test the planner: run it on a sample prompt and print the result.

Usage:
  python scripts/test_planner.py
  python scripts/test_planner.py "Your custom prompt here"

Requires .env with ANTHROPIC_API_KEY. Set LANGSMITH_API_KEY and LANGCHAIN_TRACING_V2=true
in .env to see traces at https://smith.langchain.com (optional).
"""

import os
import sys

# Project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.planner import run_planner


DEFAULT_PROMPT = "summarize the last n emails in my gmail if there is anyone needing a meeting schedule one in my google calendar"


def main() -> None:
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    print("Running planner with prompt:")
    print(f"  {prompt!r}\n")

    result = run_planner(prompt)

    print("--- Result ---")
    print("validation_result:", result.get("validation_result"))
    print("services:", result.get("services"))
    print("workflow_steps:", result.get("workflow_steps"))
    print("parameters:", result.get("parameters"))
    print("suggested_http_method:", result.get("suggested_http_method"))
    print("suggested_path_slug:", result.get("suggested_path_slug"))
    if result.get("errors"):
        print("errors:", result.get("errors"))
    print("\ntask_description:")
    print(result.get("task_description", "(none)"))


if __name__ == "__main__":
    main()
