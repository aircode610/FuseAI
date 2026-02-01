"""
Code generator: uses an LLM to generate FastAPI agent code from template + context.

Template provides structure and logic; context (from design agent) provides api_design,
task_description, services, parameters, selected_zapier_tools. The LLM produces the
full main.py — no re-implementing tool loading; everything comes from context and
core.zapier_mapper.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

# Project root (parent of core/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE_PATH = _PROJECT_ROOT / "templates" / "fastapi_base.py"
_DEPLOYED_AGENTS_DIR = _PROJECT_ROOT / "runtime" / "deployed_agents"


def _get_model() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=8192)


def _extract_code_from_response(text: str) -> str:
    """Extract Python code from LLM response (strip markdown code block if present)."""
    text = text.strip()
    # ```python ... ``` or ``` ... ```
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _generate_code_with_llm(template_content: str, context: dict[str, Any]) -> str:
    """Use LLM to generate the full main.py from template (structure) + context (data)."""
    system = (
        "You are a code generator. Generate the complete FastAPI agent Python file (main.py) that:\n"
        "1. Defines create_app(tools: list) -> FastAPI. The tools are LangChain tools passed in by the runner; do NOT call get_zapier_tools or load tools inside the agent.\n"
        "2. Uses the template for structure: same imports, path setup, _get_model, _format_request_context. Inside create_app(tools), run_agent uses the passed-in tools list directly (no _get_tools that calls Zapier).\n"
        "3. Fills config from context: TASK_DESCRIPTION, SYSTEM_PROMPT from the context (task_description, api_design). SERVICES and SELECTED_TOOL_NAMES are only for reference in comments; the actual tools are passed into create_app(tools).\n"
        "4. Registers one FastAPI route per endpoint in context.api_design.endpoints. Each route: extract path/query/body params, build request_context, set task_prompt = TASK_DESCRIPTION + request context text, call run_agent(task_prompt, SYSTEM_PROMPT) (run_agent uses the tools stored in app state or closure).\n"
        "5. create_app(tools) must store tools so run_agent can use them (e.g. app.state.tools = tools and run_agent reads from request.app.state.tools, or a closure over tools). Ensures project root is on sys.path (Path(__file__).resolve().parent.parent.parent.parent).\n"
        "Output only the Python code, no explanation. Use a markdown code block: ```python\\n...\\n```"
    )
    user = (
        "Template (reference for structure and logic):\n\n```python\n"
        + template_content
        + "\n```\n\n"
        "Context (use this data — api_design.endpoints for routes, task_description, services, selected_zapier_tools for config):\n\n"
        + json.dumps(context, indent=2)
    )
    model = _get_model()
    response = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    content = response.content if hasattr(response, "content") else str(response)
    if isinstance(content, str):
        return _extract_code_from_response(content)
    return _extract_code_from_response(str(content))


def generate_agent(
    context_for_coding_agent: dict[str, Any],
    agent_id: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    """
    Generate FastAPI agent code using an LLM: template (structure) + context (data) → main.py.

    - context_for_coding_agent: from design agent (api_design, task_description, services, parameters, selected_zapier_tools).
    - agent_id: optional; if omitted, use "agent_<timestamp>".
    - output_dir: optional; if omitted, use runtime/deployed_agents/<agent_id>/.

    Returns the path to the generated main.py.
    """
    agent_id = agent_id or f"agent_{int(time.time())}"
    out_dir = output_dir or _DEPLOYED_AGENTS_DIR / agent_id
    out_dir.mkdir(parents=True, exist_ok=True)
    main_py = out_dir / "main.py"

    template_path = _TEMPLATE_PATH
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    template_content = template_path.read_text(encoding="utf-8")

    code = _generate_code_with_llm(template_content, context_for_coding_agent)
    main_py.write_text(code, encoding="utf-8")

    # Write tools manifest so the runner can load the same tools and pass them to create_app(tools)
    tool_names = [t.get("name") for t in (context_for_coding_agent.get("selected_zapier_tools") or []) if t.get("name")]
    services = list(context_for_coding_agent.get("services") or [])
    manifest = {"tool_names": tool_names, "services": services}
    manifest_path = out_dir / "tools_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return main_py
