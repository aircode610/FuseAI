"""
Unified design agent: planner → API designer → zapier_mapper (with LLM tool selection).

Single LangGraph with shared context flowing through:
  1. Plan & design: planner + API designer on user_prompt → planner_context.
  2. Load Zapier tools: get all (or by services) from Zapier MCP → available_zapier_tools.
  3. Select tools: LLM chooses which tools are needed given planner_context → selected tools saved to context.
  4. Build context for coding agent: api_design + selected_zapier_tools (serialized).

Output: context_for_coding_agent for the coding agent to build an agent from.
"""

from __future__ import annotations

import asyncio
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from core.zapier_mapper import (
    get_planner_context,
    get_zapier_tools,
    save_tools_to_context,
    select_tools_with_llm,
)


# ---------------------------------------------------------------------------
# Shared state (context flows through)
# ---------------------------------------------------------------------------

class DesignAgentState(TypedDict, total=False):
    """State for the unified design agent. Context is shared between steps."""

    user_prompt: str
    planner_context: dict[str, Any]
    available_zapier_tools: list[Any]  # LangChain tools from Zapier MCP
    selected_tool_names: list[str]
    selected_zapier_tools: list[dict[str, Any]]  # Serialized for coding agent
    selected_tools_objects: list[Any]  # Actual LangChain tools to pass to code generator
    context_for_coding_agent: dict[str, Any]


# ---------------------------------------------------------------------------
# Node: plan_and_design
# ---------------------------------------------------------------------------

def plan_and_design(state: DesignAgentState) -> dict[str, Any]:
    """Run planner then API designer; put result in shared context."""
    user_prompt = state.get("user_prompt") or ""
    planner_context = get_planner_context(user_prompt)
    return {"planner_context": planner_context}


# ---------------------------------------------------------------------------
# Node: load_zapier_tools
# ---------------------------------------------------------------------------

async def load_zapier_tools(state: DesignAgentState) -> dict[str, Any]:
    """Load Zapier MCP tools (all, or filtered by planner services) into context."""
    planner_context = state.get("planner_context") or {}
    if not planner_context.get("valid", True):
        return {"available_zapier_tools": []}
    services = planner_context.get("services") or []
    tools = await get_zapier_tools(services=services if services else None)
    return {"available_zapier_tools": tools}


# ---------------------------------------------------------------------------
# Node: select_tools_with_llm_node
# ---------------------------------------------------------------------------

async def select_tools_with_llm_node(state: DesignAgentState) -> dict[str, Any]:
    """Use LLM to select which Zapier tools are needed; save serialized tools and actual tool objects to context."""
    planner_context = state.get("planner_context") or {}
    available = state.get("available_zapier_tools") or []
    if not available:
        return {
            "selected_tool_names": [],
            "selected_zapier_tools": [],
            "selected_tools_objects": [],
        }
    selected_names, selected_serialized = await select_tools_with_llm(planner_context, available)
    names_set = {n.strip().lower() for n in selected_names if n}
    selected_objects = [t for t in available if (getattr(t, "name", None) or "").strip().lower() in names_set]
    return {
        "selected_tool_names": selected_names,
        "selected_zapier_tools": selected_serialized,
        "selected_tools_objects": selected_objects,
    }


# ---------------------------------------------------------------------------
# Node: build_context_for_coding_agent
# ---------------------------------------------------------------------------

def build_context_for_coding_agent(state: DesignAgentState) -> dict[str, Any]:
    """Save selected tools into planner_context and set context_for_coding_agent."""
    planner_context = dict(state.get("planner_context") or {})
    selected_serialized = state.get("selected_zapier_tools") or []
    save_tools_to_context(planner_context, selected_serialized)
    context_for_coding_agent = planner_context.get("context_for_coding_agent") or {}
    return {"context_for_coding_agent": context_for_coding_agent}


# ---------------------------------------------------------------------------
# Graph: wrap async nodes so they can be used in sync graph
# ---------------------------------------------------------------------------

def _run_async(coro):
    """Run async coroutine from sync context (e.g. graph node). Uses a thread + asyncio.run."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


def node_load_zapier_tools(state: DesignAgentState) -> dict[str, Any]:
    """Sync wrapper for load_zapier_tools."""
    return _run_async(load_zapier_tools(state))


def node_select_tools_with_llm(state: DesignAgentState) -> dict[str, Any]:
    """Sync wrapper for select_tools_with_llm_node."""
    return _run_async(select_tools_with_llm_node(state))


# ---------------------------------------------------------------------------
# Build and compile the design agent graph
# ---------------------------------------------------------------------------

def build_design_agent_graph() -> StateGraph:
    """Build the unified design agent graph: plan → design → load tools → select tools (LLM) → build context."""
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
    """Compile the design agent graph (no checkpointer)."""
    graph = build_design_agent_graph()
    return graph.compile()


# Singleton for API / scripts
design_agent = create_design_agent()


# ---------------------------------------------------------------------------
# Entry point: run design agent and return context for coding agent
# ---------------------------------------------------------------------------

def run_design_agent(user_prompt: str) -> dict[str, Any]:
    """
    Run the unified design agent: planner → API designer → Zapier tool selection (LLM) → context.

    Returns the final state; state["context_for_coding_agent"] has api_design and selected_zapier_tools
    for the coding agent to build an agent from.
    """
    initial: DesignAgentState = {"user_prompt": user_prompt}
    result = design_agent.invoke(initial)
    return result


async def run_design_agent_async(user_prompt: str) -> dict[str, Any]:
    """Async entry point (runs sync invoke in thread)."""
    return await asyncio.to_thread(run_design_agent, user_prompt)
