"""
Reference template for FastAPI agent code generation (LLM uses this for structure and logic).

The code generator LLM receives this template + context_for_coding_agent and produces
the actual main.py. Tools are passed in by the runner via create_app(tools) — the
generated agent does NOT call get_zapier_tools; it uses the LangChain tools it receives.

Structure to follow:
  1. Path setup so project root is on sys.path when run from runtime/deployed_agents/<id>/main.py
  2. Imports: FastAPI, Request, langchain_anthropic, langchain_core.messages, langgraph.prebuilt.create_react_agent
  3. Config from context: TASK_DESCRIPTION, SYSTEM_PROMPT (SERVICES/SELECTED_TOOL_NAMES only for comments)
  4. def create_app(tools: list) -> FastAPI: ... store tools on app.state.tools
  5. _get_model() -> ChatAnthropic
  6. _format_request_context(ctx: dict) -> str for building task prompt
  7. run_agent(task_prompt, system_prompt, tools: list) or run_agent that reads tools from request.app.state.tools
  8. Inside create_app: app = FastAPI(), app.state.tools = tools, @app.get("/health"), one route per endpoint
  9. Each route: extract path/query/body, build request_context, task_prompt = TASK_DESCRIPTION + request_context, run_agent using app.state.tools
  10. if __name__ == "__main__": only for local dev; runner normally uses create_app(tools) and uvicorn.run(app)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Project root when run from runtime/deployed_agents/<id>/main.py (go up 4 levels)
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, Request
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

# Config: set from context (task_description, api_design; tools are passed into create_app(tools))
TASK_DESCRIPTION = ""
SYSTEM_PROMPT = ""


def _get_model():
    return ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=4096)


def _format_request_context(ctx: dict[str, Any]) -> str:
    if not ctx:
        return ""
    lines = [f"- {k}: {v}" for k, v in ctx.items() if v is not None and v != ""]
    return "Current request:\n" + "\n".join(lines) if lines else ""


async def run_agent(task_prompt: str, system_prompt: str, tools: list) -> dict[str, Any]:
    if not tools:
        return {"success": False, "result": "", "error": "No tools provided."}
    try:
        model = _get_model()
        agent = create_react_agent(model, tools)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=task_prompt)]
        result = await agent.ainvoke({"messages": messages})
        msg_list = result.get("messages") or []
        last_content = ""
        for m in reversed(msg_list):
            if hasattr(m, "content") and isinstance(m.content, str) and m.content.strip():
                last_content = m.content.strip()
                break
        return {"success": True, "result": last_content or str(result), "error": None}
    except Exception as e:
        return {"success": False, "result": "", "error": f"Request processing error: {e!r}"}


def create_app(tools: list) -> FastAPI:
    """Create FastAPI app with the given LangChain tools (passed in by the runner)."""
    app = FastAPI(title="Generated Agent", version="1.0.0")
    app.state.tools = tools

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # One route per endpoint from context api_design.endpoints
    # Example: @app.post("/path/{path_param}"), async def handler(request: Request, path_param: str):
    #   request_context = {...}, task_prompt = TASK_DESCRIPTION + _format_request_context(request_context)
    #   return await run_agent(task_prompt, SYSTEM_PROMPT, request.app.state.tools)

    return app


if __name__ == "__main__":
    import uvicorn
    # When run directly, no tools; use create_app([]) for health-only or load from manifest
    app = create_app([])
    uvicorn.run(app, host="0.0.0.0", port=8000)
