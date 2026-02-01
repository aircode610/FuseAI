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

    # Per-agent config.json, README.md, requirements.txt for Code tab
    agent_name = (context_for_coding_agent.get("suggested_agent_name") or "").strip() or "Generated Agent"
    task_description = (context_for_coding_agent.get("task_description") or "").strip()
    api_design = context_for_coding_agent.get("api_design") or {}
    endpoints = api_design.get("endpoints") or []

    config = {
        "agent_id": agent_id,
        "name": agent_name,
        "trigger_type": "on_demand",
        "zapier": {
            "services": services,
            "tool_names": tool_names,
        },
        "monitoring": {
            "log_level": "INFO",
            "enable_metrics": True,
        },
    }
    (out_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    readme_lines = [
        f"# {agent_name}",
        "",
        task_description[:500] if task_description else "Auto-generated agent by FuseAI.",
        "",
        "## Setup",
        "",
        "1. Install dependencies:",
        "```bash",
        "pip install -r requirements.txt",
        "```",
        "",
        "2. Set environment variables (e.g. in .env):",
        "```bash",
        "export ANTHROPIC_API_KEY=your_key",
        "export ZAPIER_MCP_SERVER_URL=...",
        "export ZAPIER_MCP_SECRET=...",
        "```",
        "",
        "3. Run the server:",
        "```bash",
        "uvicorn main:app --host 0.0.0.0 --port 8000",
        "```",
        "",
        "## API Endpoints",
        "",
    ]
    for ep in endpoints:
        method = (ep.get("method") or "POST").upper()
        path = ep.get("path") or "/execute"
        summary = (ep.get("summary") or "").strip()
        readme_lines.append(f"### {method} {path}")
        if summary:
            readme_lines.append(f"\n{summary}\n")
    (out_dir / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")

    requirements = """fastapi>=0.109.0
uvicorn>=0.27.0
httpx>=0.26.0
python-dotenv>=1.0.0
pydantic>=2.5.0
langchain-anthropic>=0.2.0
langchain-core>=0.3.0
langgraph>=0.2.0
"""
    (out_dir / "requirements.txt").write_text(requirements, encoding="utf-8")

    return main_py
