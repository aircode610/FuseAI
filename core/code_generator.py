# Code generator: LLM generates FastAPI main.py from template + context_for_coding_agent.

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from core.prompts import CODE_GEN_SYSTEM

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE_PATH = _PROJECT_ROOT / "templates" / "fastapi_base.py"
_DEPLOYED_AGENTS_DIR = _PROJECT_ROOT / "runtime" / "deployed_agents"


def _get_model() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=8192)


def _extract_code_from_response(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _generate_code_with_llm(template_content: str, context: dict[str, Any]) -> str:
    user = (
        "Template (reference for structure and logic):\n\n```python\n"
        + template_content
        + "\n```\n\n"
        "Context (use this data — api_design.endpoints for routes, task_description, services, selected_zapier_tools for config):\n\n"
        + json.dumps(context, indent=2)
    )
    model = _get_model()
    response = model.invoke([SystemMessage(content=CODE_GEN_SYSTEM), HumanMessage(content=user)])
    content = response.content if hasattr(response, "content") else str(response)
    if isinstance(content, str):
        return _extract_code_from_response(content)
    return _extract_code_from_response(str(content))


def generate_agent(
    context_for_coding_agent: dict[str, Any],
    agent_id: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    agent_id = agent_id or f"agent_{int(time.time())}"
    out_dir = output_dir or _DEPLOYED_AGENTS_DIR / agent_id
    out_dir.mkdir(parents=True, exist_ok=True)
    main_py = out_dir / "main.py"
    if not _TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {_TEMPLATE_PATH}")
    template_content = _TEMPLATE_PATH.read_text(encoding="utf-8")
    code = _generate_code_with_llm(template_content, context_for_coding_agent)
    main_py.write_text(code, encoding="utf-8")
    tool_names = [t.get("name") for t in (context_for_coding_agent.get("selected_zapier_tools") or []) if t.get("name")]
    services = list(context_for_coding_agent.get("services") or [])
    manifest = {"tool_names": tool_names, "services": services}
    (out_dir / "tools_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return main_py
