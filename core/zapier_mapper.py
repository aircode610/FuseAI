# Zapier MCP: planner + API design → load tools → LLM tool selection → save to context_for_coding_agent.

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Any

from core.models import SelectedToolsOutput
from core.prompts import format_tool_selection

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


def get_planner_context(user_prompt: str) -> dict[str, Any]:
    from core.api_designer import run_api_designer
    from core.planner import run_planner
    state = run_planner(user_prompt)
    validation = state.get("validation_result") or {}
    valid = validation.get("valid", True)
    services = list(state.get("services") or [])
    workflow_steps = list(state.get("workflow_steps") or [])
    task_description = (state.get("task_description") or "").strip()
    parameters = list(state.get("parameters") or [])
    suggested_agent_name = (state.get("suggested_agent_name") or "").strip()
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
        "workflow_steps": workflow_steps,
        "task_description": task_description,
        "parameters": parameters,
        "api_design": design_dict,
        "valid": valid,
        "validation_reason": validation.get("reason") if not valid else None,
        "suggested_agent_name": suggested_agent_name or None,
    }


def _get_zapier_client() -> Any:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    url = os.environ.get("ZAPIER_MCP_SERVER_URL", "").strip()
    secret = os.environ.get("ZAPIER_MCP_SECRET", "").strip()
    if not url or not secret:
        raise ValueError(
            "ZAPIER_MCP_SERVER_URL and ZAPIER_MCP_SECRET must be set. Get them from https://mcp.zapier.com"
        )
    return MultiServerMCPClient(
        {"zapier": {"transport": "http", "url": url.rstrip("/"), "headers": {"Authorization": f"Bearer {secret}"}}}
    )


def _tool_matches_services(tool: "BaseTool", services: list[str]) -> bool:
    if not services:
        return True
    name = (getattr(tool, "name", None) or "").lower()
    desc = (getattr(tool, "description", None) or "").lower()
    combined = f"{name} {desc}"
    for s in services:
        if not (s or "").strip():
            continue
        raw = (s or "").strip().lower()
        if raw in combined:
            return True
        if raw.replace(" ", "_") in combined:
            return True
        if raw.replace(" ", "") in combined:
            return True
        words = [w for w in raw.split() if len(w) > 1]
        if words and all(w in combined for w in words):
            return True
    return False


async def get_zapier_tools(services: list[str] | None = None) -> list["BaseTool"]:
    client = _get_zapier_client()
    tools = await client.get_tools()
    tool_list = list(tools)
    if not services or not [s for s in services if (s or "").strip()]:
        return tool_list
    return [t for t in tool_list if _tool_matches_services(t, services)]


def serialize_tool_for_context(tool: "BaseTool") -> dict[str, Any]:
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
        except Exception:
            pass
    return {"name": name, "description": description, "args_schema": args_schema}


def _get_tool_selection_model() -> Any:
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=1024)


def _build_tool_list_for_llm(tools: list["BaseTool"]) -> str:
    lines = []
    for i, t in enumerate(tools):
        name = getattr(t, "name", None) or ""
        desc = (getattr(t, "description", None) or "").strip()
        lines.append(f"{i + 1}. {name}: {desc[:200]}{'...' if len(desc or '') > 200 else ''}")
    return "\n".join(lines) if lines else "(no tools available)"


def select_tools_with_llm_sync(context: dict[str, Any], available_tools: list["BaseTool"]) -> tuple[list[str], list[dict[str, Any]]]:
    if not available_tools:
        return ([], [])
    task = context.get("task_description") or ""
    services = context.get("services") or []
    api_design = context.get("api_design") or {}
    endpoints_summary = ""
    if api_design.get("endpoints"):
        endpoints_summary = "\n".join(f"- {ep.get('method')} {ep.get('path')}: {ep.get('summary')}" for ep in api_design["endpoints"])
    tool_list_text = _build_tool_list_for_llm(available_tools)
    services_str = ", ".join(services) if services else "Not specified"
    system, user = format_tool_selection(task, services_str, endpoints_summary, tool_list_text)
    from langchain_core.messages import HumanMessage, SystemMessage
    model = _get_tool_selection_model().with_structured_output(SelectedToolsOutput)
    out = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    selected_names = list(out.tool_names or [])
    selected_names_normalized = {n.strip().lower() for n in selected_names if n}
    selected_tools = [t for t in available_tools if (getattr(t, "name", None) or "").strip().lower() in selected_names_normalized]
    if not selected_tools and selected_names:
        for t in available_tools:
            name = (getattr(t, "name", None) or "").lower()
            if any(sn.lower() in name or name in sn.lower() for sn in selected_names if sn):
                selected_tools.append(t)
    selected_serialized = [serialize_tool_for_context(t) for t in selected_tools]
    return ([getattr(t, "name", "") for t in selected_tools], selected_serialized)


async def select_tools_with_llm(context: dict[str, Any], available_tools: list["BaseTool"]) -> tuple[list[str], list[dict[str, Any]]]:
    return await asyncio.to_thread(select_tools_with_llm_sync, context, available_tools)


def save_tools_to_context(context: dict[str, Any], selected_tools_serialized: list[dict[str, Any]]) -> None:
    context["selected_zapier_tools"] = selected_tools_serialized
    context["context_for_coding_agent"] = {
        "api_design": context.get("api_design", {}),
        "task_description": context.get("task_description", ""),
        "workflow_steps": context.get("workflow_steps", []),
        "services": context.get("services", []),
        "parameters": context.get("parameters", []),
        "selected_zapier_tools": selected_tools_serialized,
        "suggested_agent_name": context.get("suggested_agent_name") or "",
    }
