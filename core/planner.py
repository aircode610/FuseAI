"""
Planner: agent that validates user prompts and extracts requirements via LLM.

Uses LangGraph for state and node execution. Each node calls a LangChain chat
model with structured output (Pydantic schemas), so responses are parsed and
validated by the framework—no manual JSON parsing.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from core.planner_prompts import (
    format_extract_parameters,
    format_extract_services,
    format_suggest_endpoint,
    format_validate_task,
)

# ---------------------------------------------------------------------------
# Pydantic schemas for structured LLM output (no manual JSON parsing)
# ---------------------------------------------------------------------------


class ValidateOutput(BaseModel):
    """LLM output for validate_task step."""

    valid: bool = Field(description="True if the input is a coherent workflow task")
    reason: str = Field(description="One short sentence explaining why")


class ServicesOutput(BaseModel):
    """LLM output for extract_services step."""

    services: list[str] = Field(
        default_factory=list,
        description="Distinct service/app names mentioned (e.g. Trello, Slack)",
    )


class ParameterItem(BaseModel):
    """One API parameter for extract_parameters step."""

    name: str = Field(description="snake_case parameter name")
    type: str = Field(default="str", description="str, int, or bool")
    description: str = Field(default="", description="What this parameter is for")
    required: bool = Field(default=True, description="Whether the parameter is required")
    location: Literal["path", "query", "body"] = Field(
        default="body",
        description="path, query, or body",
    )
    how_used: str = Field(default="", description="How this parameter is used in the task")


class ParametersOutput(BaseModel):
    """LLM output for extract_parameters step."""

    parameters: list[ParameterItem] = Field(default_factory=list, description="API parameters")


class EndpointOutput(BaseModel):
    """LLM output for suggest_endpoint step."""

    method: str = Field(default="POST", description="GET, POST, PUT, DELETE, or PATCH")
    path_slug: str = Field(default="execute", description="Short hyphenated slug, no leading slash")


# ---------------------------------------------------------------------------
# Agent state schema (LangGraph state only)
# ---------------------------------------------------------------------------

ParamLocation = Literal["path", "query", "body"]


class ParameterSpec(TypedDict, total=False):
    """A single parameter for the REST endpoint (path/query/body) with usage."""

    name: str
    type: str
    description: str
    required: bool
    location: ParamLocation
    how_used: str


class ValidationResult(TypedDict, total=False):
    """Result of validate_task step."""

    valid: bool
    reason: str


class PlannerState(TypedDict, total=False):
    """State for the planner graph. All updates go through LangGraph."""

    user_prompt: str
    validation_result: ValidationResult
    services: list[str]
    parameters: list[ParameterSpec]
    suggested_http_method: str
    suggested_path_slug: str
    task_description: str
    errors: Annotated[list[str], lambda a, b: (a or []) + (b or [])]


# ---------------------------------------------------------------------------
# LLM: LangChain structured output (returns Pydantic instances, no JSON parsing)
# ---------------------------------------------------------------------------

def _get_model():
    """Return the chat model. Lazy init, used by nodes."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        raise ImportError(
            "langchain-anthropic and langchain-core are required for the planner. "
            "Install with: pip install langchain-anthropic langchain-core"
        ) from e
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
    )


def _invoke_structured(system: str, user: str, schema: type[BaseModel]) -> BaseModel:
    """Invoke the model with structured output; returns a Pydantic instance."""
    from langchain_core.messages import HumanMessage, SystemMessage

    model = _get_model().with_structured_output(schema)
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    return model.invoke(messages)


# ---------------------------------------------------------------------------
# Node: validate_task
# ---------------------------------------------------------------------------

def validate_task(state: PlannerState) -> dict[str, Any]:
    """Validate the user prompt as a workflow task. Uses VALIDATE_TASK prompt."""
    user_prompt = state.get("user_prompt") or ""
    system, user = format_validate_task(user_prompt)
    try:
        out = _invoke_structured(system, user, ValidateOutput)
        return {
            "validation_result": {"valid": out.valid, "reason": out.reason},
            "errors": [] if out.valid else [out.reason],
        }
    except Exception as e:
        return {
            "validation_result": {"valid": False, "reason": str(e)},
            "errors": [f"Validation step failed: {e}"],
        }


# ---------------------------------------------------------------------------
# Node: extract_services
# ---------------------------------------------------------------------------

def extract_services(state: PlannerState) -> dict[str, Any]:
    """Extract services from the user prompt. Uses EXTRACT_SERVICES prompt."""
    user_prompt = state.get("user_prompt") or ""
    system, user = format_extract_services(user_prompt)
    try:
        out = _invoke_structured(system, user, ServicesOutput)
        return {"services": [s.strip() for s in out.services if s]}
    except Exception as e:
        return {"services": [], "errors": [f"Extract services failed: {e}"]}


# ---------------------------------------------------------------------------
# Node: extract_parameters
# ---------------------------------------------------------------------------

def extract_parameters(state: PlannerState) -> dict[str, Any]:
    """Extract parameters and how they are used. Uses EXTRACT_PARAMETERS prompt."""
    user_prompt = state.get("user_prompt") or ""
    services = state.get("services") or []
    system, user = format_extract_parameters(user_prompt, services)
    try:
        out = _invoke_structured(system, user, ParametersOutput)
        parameters: list[ParameterSpec] = [
            {
                "name": p.name or "param",
                "type": p.type or "str",
                "description": p.description,
                "required": p.required,
                "location": p.location,
                "how_used": p.how_used,
            }
            for p in out.parameters
        ]
        return {"parameters": parameters}
    except Exception as e:
        return {"parameters": [], "errors": [f"Extract parameters failed: {e}"]}


# ---------------------------------------------------------------------------
# Node: suggest_endpoint
# ---------------------------------------------------------------------------

def suggest_endpoint(state: PlannerState) -> dict[str, Any]:
    """Suggest HTTP method and path slug. Uses SUGGEST_ENDPOINT prompt."""
    user_prompt = state.get("user_prompt") or ""
    services = state.get("services") or []
    system, user = format_suggest_endpoint(user_prompt, services)
    try:
        out = _invoke_structured(system, user, EndpointOutput)
        method = (out.method or "POST").upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            method = "POST"
        path_slug = (out.path_slug or "execute").strip().strip("/").replace(" ", "-")
        return {"suggested_http_method": method, "suggested_path_slug": path_slug or "execute"}
    except Exception as e:
        return {
            "suggested_http_method": "POST",
            "suggested_path_slug": "execute",
            "errors": [f"Suggest endpoint failed: {e}"],
        }


# ---------------------------------------------------------------------------
# Node: format_task_description (no LLM—assemble from state)
# ---------------------------------------------------------------------------

def format_task_description(state: PlannerState) -> dict[str, Any]:
    """Assemble task description from state for the API designer. No LLM call."""
    user_prompt = state.get("user_prompt") or ""
    services = state.get("services") or []
    parameters = state.get("parameters") or []
    method = state.get("suggested_http_method") or "POST"
    path_slug = state.get("suggested_path_slug") or "execute"

    parts = [
        f"Task: {user_prompt}",
        f"Suggested endpoint: {method} /{path_slug}",
    ]
    if services:
        parts.append(f"Services: {', '.join(services)}")
    if parameters:
        param_lines = []
        for p in parameters:
            loc = p.get("location", "body")
            how = p.get("how_used", "")
            param_lines.append(f"- {p.get('name', '')} ({p.get('type', 'str')}, {loc}): {how or p.get('description', '')}")
        parts.append("Parameters:\n" + "\n".join(param_lines))

    return {"task_description": "\n".join(parts)}


# ---------------------------------------------------------------------------
# Build and compile the planner graph (LangGraph StateGraph + context_schema)
# ---------------------------------------------------------------------------

def build_planner_graph() -> StateGraph:
    """
    Build the planner graph: validate_task -> extract_services -> extract_parameters
    -> suggest_endpoint -> format_task_description.
    State is kept by LangGraph; nodes read state and return updates.
    """
    builder: StateGraph = StateGraph(PlannerState)

    builder.add_node("validate_task", validate_task)
    builder.add_node("extract_services", extract_services)
    builder.add_node("extract_parameters", extract_parameters)
    builder.add_node("suggest_endpoint", suggest_endpoint)
    builder.add_node("format_task_description", format_task_description)

    builder.add_edge(START, "validate_task")
    builder.add_edge("validate_task", "extract_services")
    builder.add_edge("extract_services", "extract_parameters")
    builder.add_edge("extract_parameters", "suggest_endpoint")
    builder.add_edge("suggest_endpoint", "format_task_description")
    builder.add_edge("format_task_description", END)

    return builder


def create_planner() -> Any:
    """Compile and return the planner graph (invokable)."""
    return build_planner_graph().compile()


def run_planner(user_prompt: str) -> dict[str, Any]:
    """Run the planner on a single user prompt. Returns the final state from LangGraph."""
    graph = create_planner()
    initial: PlannerState = {"user_prompt": user_prompt}
    return graph.invoke(initial)


# Compiled graph for LangGraph Studio / langgraph dev (see docs/TESTING.md)
planner = create_planner()
