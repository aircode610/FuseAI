"""
Zapier MCP: plan → API design → select tools (with LLM) → save to context.

Single flow with shared context:
  1. Planner (core.planner) runs on the user prompt → services, parameters, task_description.
  2. API designer (core.api_designer) runs on planner state → endpoints, task_description.
  3. Zapier MCP tools are loaded (all or by services).
  4. An LLM selects which tools are needed given the planner + API design context.
  5. Selected tools are serialized and saved into context for the coding agent.

Configure your MCP server at https://mcp.zapier.com and set ZAPIER_MCP_SERVER_URL
and ZAPIER_MCP_SECRET in .env.
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

# ---------------------------------------------------------------------------
# Planner + API designer context (step 1 & 2)
# ---------------------------------------------------------------------------

def get_planner_context(user_prompt: str) -> dict[str, Any]:
    """
    Run planner then API designer on the task prompt.

    Returns context for tool selection and coding agent:
      - services: list[str] — e.g. ["Trello", "Slack"].
      - task_description: str — full task text from planner/designer.
      - parameters: list[dict] — from planner.
      - api_design: dict — endpoints, services, task_description.
      - valid: bool — False if planner validation failed.
      - validation_reason: str | None — when valid is False.
    """
    from core.api_designer import run_api_designer
    from core.planner import run_planner

    state = run_planner(user_prompt)
    validation = state.get("validation_result") or {}
    valid = validation.get("valid", True)

    services = list(state.get("services") or [])
    task_description = (state.get("task_description") or "").strip()
    parameters = list(state.get("parameters") or [])

    api_design = run_api_designer(state)
    design_task = (api_design.task_description or "").strip()
    if design_task and len(design_task) >= len(task_description):
        task_description = design_task
    if not task_description and design_task:
        task_description = design_task

    design_dict: dict[str, Any] = {
        "endpoints": [
            {
                "method": ep.method,
                "path": ep.path,
                "operation_id": ep.operation_id,
                "summary": ep.summary,
                "path_parameters": [p.model_dump() for p in ep.path_parameters],
                "query_parameters": [p.model_dump() for p in ep.query_parameters],
                "body_parameters": [p.model_dump() for p in ep.body_parameters],
            }
            for ep in api_design.endpoints
        ],
        "services": list(api_design.services),
        "task_description": api_design.task_description or "",
    }

    return {
        "services": services,
        "task_description": task_description,
        "parameters": parameters,
        "api_design": design_dict,
        "valid": valid,
        "validation_reason": validation.get("reason") if not valid else None,
    }


# ---------------------------------------------------------------------------
# Zapier MCP client and tools (step 3)
# ---------------------------------------------------------------------------

def _get_zapier_client() -> Any:
    """Return MultiServerMCPClient for Zapier MCP. Lazy to avoid import errors."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    url = os.environ.get("ZAPIER_MCP_SERVER_URL", "").strip()
    secret = os.environ.get("ZAPIER_MCP_SECRET", "").strip()
    if not url or not secret:
        raise ValueError(
            "ZAPIER_MCP_SERVER_URL and ZAPIER_MCP_SECRET must be set to use Zapier MCP. "
            "Get them from https://mcp.zapier.com when creating/connecting your MCP server."
        )
    return MultiServerMCPClient(
        {
            "zapier": {
                "transport": "http",
                "url": url.rstrip("/"),
                "headers": {"Authorization": f"Bearer {secret}"},
            }
        }
    )


def _tool_matches_services(tool: "BaseTool", services: list[str]) -> bool:
    """True if the tool's name/description mention any of the given services.

    Matches normalized forms so e.g. 'Google Calendar' matches tool names like
    'google_calendar_create_event' or descriptions containing 'Google Calendar'.
    """
    if not services:
        return True
    name = (getattr(tool, "name", None) or "").lower()
    desc = (getattr(tool, "description", None) or "").lower()
    combined = f"{name} {desc}"

    for s in services:
        if not (s or "").strip():
            continue
        raw = (s or "").strip().lower()
        # Exact phrase (e.g. "google calendar")
        if raw in combined:
            return True
        # With underscore (e.g. "google_calendar")
        if raw.replace(" ", "_") in combined:
            return True
        # No space (e.g. "googlecalendar")
        if raw.replace(" ", "") in combined:
            return True
        # All words present (e.g. "google" and "calendar" in "google_calendar create event")
        words = [w for w in raw.split() if len(w) > 1]
        if words and all(w in combined for w in words):
            return True
    return False


async def get_zapier_tools(services: list[str] | None = None) -> list["BaseTool"]:
    """
    Load Zapier MCP tools, optionally filtered by service names.

    - services: If provided, only tools whose name/description mention those apps.
      If None or empty, all tools are returned.
    """
    client = _get_zapier_client()
    tools = await client.get_tools()
    tool_list = list(tools)

    if not services or not [s for s in services if (s or "").strip()]:
        return tool_list

    return [t for t in tool_list if _tool_matches_services(t, services)]


# ---------------------------------------------------------------------------
# Serialize tools for context (for coding agent)
# ---------------------------------------------------------------------------

def serialize_tool_for_context(tool: "BaseTool") -> dict[str, Any]:
    """Serialize a LangChain tool for context_for_coding_agent (name, description, args_schema)."""
    name = getattr(tool, "name", None) or ""
    description = getattr(tool, "description", None) or ""
    args_schema: dict[str, Any] = {}
    if getattr(tool, "args_schema", None) is not None:
        schema = tool.args_schema
        try:
            if hasattr(schema, "model_json_schema"):
                args_schema = schema.model_json_schema()
            elif hasattr(schema, "schema"):
                args_schema = schema.schema() if callable(getattr(schema, "schema")) else {}
            else:
                args_schema = {}
        except Exception:
            args_schema = {}
    return {
        "name": name,
        "description": description,
        "args_schema": args_schema,
    }


# ---------------------------------------------------------------------------
# LLM-based tool selection (step 4) and save to context (step 5)
# ---------------------------------------------------------------------------

def _get_tool_selection_model() -> Any:
    """Chat model for tool selection. Lazy import."""
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=1024)


def _build_tool_list_for_llm(tools: list["BaseTool"]) -> str:
    """Build a text list of tool names and descriptions for the LLM."""
    lines = []
    for i, t in enumerate(tools):
        name = getattr(t, "name", None) or ""
        desc = (getattr(t, "description", None) or "").strip()
        lines.append(f"{i + 1}. {name}: {desc[:200]}{'...' if len(desc or '') > 200 else ''}")
    return "\n".join(lines) if lines else "(no tools available)"


def select_tools_with_llm_sync(context: dict[str, Any], available_tools: list["BaseTool"]) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Use an LLM to select which Zapier tools are needed given planner + API design context.

    - context: from get_planner_context (task_description, services, api_design).
    - available_tools: full list of LangChain tools from Zapier MCP.

    Returns (selected_tool_names, selected_tools_serialized).
    selected_tools_serialized is a list of dicts (name, description, args_schema) for the coding agent.
    """
    from pydantic import BaseModel, Field

    class SelectedToolsOutput(BaseModel):
        tool_names: list[str] = Field(
            description="Exact names of the Zapier tools to use for this task (subset of the available list). Use only the tool name as shown, e.g. 'Find Board' or 'Send Channel Message'.",
        )

    if not available_tools:
        return ([], [])

    task = context.get("task_description") or ""
    services = context.get("services") or []
    api_design = context.get("api_design") or {}
    endpoints_summary = ""
    if api_design.get("endpoints"):
        endpoints_summary = "\n".join(
            f"- {ep.get('method')} {ep.get('path')}: {ep.get('summary')}"
            for ep in api_design["endpoints"]
        )

    tool_list_text = _build_tool_list_for_llm(available_tools)
    tool_names = [getattr(t, "name", None) or "" for t in available_tools]

    system = (
        "You are selecting which Zapier MCP tools are needed to implement the given task and API design. "
        "Return only the exact tool names (as listed) that are necessary. Do not add tools that are not in the list. "
        "Prefer a minimal set that covers the task and the API endpoints."
    )
    user = (
        f"Task and context:\n{task}\n\n"
        f"Services involved: {', '.join(services) if services else 'Not specified'}\n\n"
        f"API endpoints:\n{endpoints_summary}\n\n"
        f"Available Zapier tools (name and description):\n{tool_list_text}\n\n"
        f"Which tool names from the list above are needed? Return only the exact names as they appear."
    )

    model = _get_tool_selection_model().with_structured_output(SelectedToolsOutput)
    from langchain_core.messages import HumanMessage, SystemMessage
    out = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    selected_names = list(out.tool_names or [])

    # Match by name (case-insensitive, strip)
    selected_names_normalized = {n.strip().lower() for n in selected_names if n}
    selected_tools = [t for t in available_tools if (getattr(t, "name", None) or "").strip().lower() in selected_names_normalized]
    # If LLM returned names that don't match exactly, try substring match
    if not selected_tools and selected_names:
        for t in available_tools:
            name = (getattr(t, "name", None) or "").lower()
            if any(sn.lower() in name or name in sn.lower() for sn in selected_names if sn):
                selected_tools.append(t)
    selected_serialized = [serialize_tool_for_context(t) for t in selected_tools]

    return ([getattr(t, "name", "") for t in selected_tools], selected_serialized)


async def select_tools_with_llm(context: dict[str, Any], available_tools: list["BaseTool"]) -> tuple[list[str], list[dict[str, Any]]]:
    """Async wrapper for select_tools_with_llm_sync (run in thread)."""
    return await asyncio.to_thread(select_tools_with_llm_sync, context, available_tools)


def save_tools_to_context(context: dict[str, Any], selected_tools_serialized: list[dict[str, Any]]) -> None:
    """
    Save selected Zapier tools into the shared context for the coding agent.

    Mutates context in place: adds context["selected_zapier_tools"] and
    context["context_for_coding_agent"] with api_design + selected_zapier_tools.
    """
    context["selected_zapier_tools"] = selected_tools_serialized
    context["context_for_coding_agent"] = {
        "api_design": context.get("api_design", {}),
        "task_description": context.get("task_description", ""),
        "services": context.get("services", []),
        "parameters": context.get("parameters", []),
        "selected_zapier_tools": selected_tools_serialized,
    }
