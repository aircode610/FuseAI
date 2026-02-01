# Design agent: planner → API designer → load Zapier tools → LLM tool selection → context for coding agent.

from __future__ import annotations

import asyncio
from typing import Any

from langgraph.graph import END, START, StateGraph

from core.models import DesignAgentState
from core.zapier_mapper import (
    get_planner_context,
    get_zapier_tools,
    save_tools_to_context,
    select_tools_with_llm,
)


def plan_and_design(state: DesignAgentState) -> dict[str, Any]:
    user_prompt = state.get("user_prompt") or ""
    planner_context = get_planner_context(user_prompt)
    return {"planner_context": planner_context}


async def load_zapier_tools(state: DesignAgentState) -> dict[str, Any]:
    planner_context = state.get("planner_context") or {}
    if not planner_context.get("valid", True):
        return {"available_zapier_tools": []}
    services = planner_context.get("services") or []
    tools = await get_zapier_tools(services=services if services else None)
    return {"available_zapier_tools": tools}


async def select_tools_with_llm_node(state: DesignAgentState) -> dict[str, Any]:
    planner_context = state.get("planner_context") or {}
    available = state.get("available_zapier_tools") or []
    if not available:
        return {"selected_tool_names": [], "selected_zapier_tools": [], "selected_tools_objects": []}
    selected_names, selected_serialized = await select_tools_with_llm(planner_context, available)
    names_set = {n.strip().lower() for n in selected_names if n}
    selected_objects = [t for t in available if (getattr(t, "name", None) or "").strip().lower() in names_set]
    return {
        "selected_tool_names": selected_names,
        "selected_zapier_tools": selected_serialized,
        "selected_tools_objects": selected_objects,
    }


def build_context_for_coding_agent(state: DesignAgentState) -> dict[str, Any]:
    planner_context = dict(state.get("planner_context") or {})
    selected_serialized = state.get("selected_zapier_tools") or []
    save_tools_to_context(planner_context, selected_serialized)
    context_for_coding_agent = planner_context.get("context_for_coding_agent") or {}
    return {"context_for_coding_agent": context_for_coding_agent}


def _run_async(coro):
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


def node_load_zapier_tools(state: DesignAgentState) -> dict[str, Any]:
    return _run_async(load_zapier_tools(state))


def node_select_tools_with_llm(state: DesignAgentState) -> dict[str, Any]:
    return _run_async(select_tools_with_llm_node(state))


def build_design_agent_graph() -> StateGraph:
    builder: StateGraph = StateGraph(DesignAgentState)
    builder.add_node("plan_and_design", plan_and_design)
    builder.add_node("load_zapier_tools", node_load_zapier_tools)
    builder.add_node("select_tools_with_llm", node_select_tools_with_llm)
    builder.add_node("build_context_for_coding_agent", build_context_for_coding_agent)
    builder.add_edge(START, "plan_and_design")
    builder.add_edge("plan_and_design", "load_zapier_tools")
    builder.add_edge("load_zapier_tools", "select_tools_with_llm")
    builder.add_edge("select_tools_with_llm", "build_context_for_coding_agent")
    builder.add_edge("build_context_for_coding_agent", END)
    return builder


def create_design_agent():
    return build_design_agent_graph().compile()


design_agent = create_design_agent()


def run_design_agent(user_prompt: str) -> dict[str, Any]:
    initial: DesignAgentState = {"user_prompt": user_prompt}
    return design_agent.invoke(initial)


async def run_design_agent_async(user_prompt: str) -> dict[str, Any]:
    return await asyncio.to_thread(run_design_agent, user_prompt)
