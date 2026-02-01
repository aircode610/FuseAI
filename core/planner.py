# Planner: validate prompt, extract services/parameters/endpoints via LLM; LangGraph state.

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from core.models import (
    EndpointHint,
    EndpointsOutput,
    ParameterItem,
    ParametersOutput,
    ParameterSpec,
    PlannerState,
    ServicesOutput,
    ValidateOutput,
    WorkflowStepItem,
    WorkflowStepsOutput,
)
from core.prompts import (
    format_extract_parameters,
    format_extract_services,
    format_extract_workflow_steps,
    format_suggest_endpoint,
    format_validate_task,
)


def _get_model():
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        raise ImportError(
            "langchain-anthropic and langchain-core are required. pip install langchain-anthropic langchain-core"
        ) from e
    return ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=1024)


def _invoke_structured(system: str, user: str, schema: type) -> Any:
    from langchain_core.messages import HumanMessage, SystemMessage
    model = _get_model().with_structured_output(schema)
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    return model.invoke(messages)


def validate_task(state: PlannerState) -> dict[str, Any]:
    user_prompt = state.get("user_prompt") or ""
    system, user = format_validate_task(user_prompt)
    try:
        out = _invoke_structured(system, user, ValidateOutput)
        return {"validation_result": {"valid": out.valid, "reason": out.reason}, "errors": [] if out.valid else [out.reason]}
    except Exception as e:
        return {"validation_result": {"valid": False, "reason": str(e)}, "errors": [f"Validation step failed: {e}"]}


def extract_services(state: PlannerState) -> dict[str, Any]:
    user_prompt = state.get("user_prompt") or ""
    system, user = format_extract_services(user_prompt)
    try:
        out = _invoke_structured(system, user, ServicesOutput)
        return {"services": [s.strip() for s in out.services if s]}
    except Exception as e:
        return {"services": [], "errors": [f"Extract services failed: {e}"]}


def extract_workflow_steps(state: PlannerState) -> dict[str, Any]:
    user_prompt = state.get("user_prompt") or ""
    services = state.get("services") or []
    system, user = format_extract_workflow_steps(user_prompt, services)
    try:
        out = _invoke_structured(system, user, WorkflowStepsOutput)
        steps_list = out.steps or []
        # Normalize (handle Pydantic model or dict) and sort by step_index
        steps_dicts: list[dict[str, Any]] = []
        for s in steps_list:
            if hasattr(s, "model_dump"):
                s = s.model_dump()
            if isinstance(s, dict):
                steps_dicts.append({
                    "step_index": s.get("step_index", len(steps_dicts) + 1),
                    "action": (s.get("action") or "").strip(),
                    "service_hint": (s.get("service_hint") or "").strip(),
                    "description": (s.get("description") or "").strip(),
                })
            elif isinstance(s, WorkflowStepItem):
                steps_dicts.append({
                    "step_index": getattr(s, "step_index", len(steps_dicts) + 1),
                    "action": (getattr(s, "action", None) or "").strip(),
                    "service_hint": (getattr(s, "service_hint", None) or "").strip(),
                    "description": (getattr(s, "description", None) or "").strip(),
                })
        steps_dicts.sort(key=lambda x: x["step_index"])
        return {"workflow_steps": steps_dicts}
    except Exception as e:
        return {"workflow_steps": [], "errors": [f"Extract workflow steps failed: {e}"]}


def extract_parameters(state: PlannerState) -> dict[str, Any]:
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
                "endpoint_index": getattr(p, "endpoint_index", 0),
            }
            for p in out.parameters
        ]
        return {"parameters": parameters}
    except Exception as e:
        return {"parameters": [], "errors": [f"Extract parameters failed: {e}"]}


def suggest_endpoint(state: PlannerState) -> dict[str, Any]:
    user_prompt = state.get("user_prompt") or ""
    services = state.get("services") or []
    system, user = format_suggest_endpoint(user_prompt, services)
    try:
        out = _invoke_structured(system, user, EndpointsOutput)
        endpoints_list = out.endpoints or []
        if not endpoints_list:
            endpoints_list = [EndpointHint(method="POST", path_slug="execute", summary="Execute the workflow")]
        suggested_endpoints: list[dict[str, Any]] = []
        for e in endpoints_list:
            method = (e.method or "POST").upper()
            if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                method = "POST"
            path_slug = (e.path_slug or "execute").strip().strip("/").replace(" ", "-") or "execute"
            suggested_endpoints.append({"method": method, "path_slug": path_slug, "summary": (e.summary or "").strip()})
        first = suggested_endpoints[0]
        return {"suggested_endpoints": suggested_endpoints, "suggested_http_method": first["method"], "suggested_path_slug": first["path_slug"], "errors": []}
    except Exception as e:
        return {
            "suggested_endpoints": [{"method": "POST", "path_slug": "execute", "summary": "Execute the workflow"}],
            "suggested_http_method": "POST",
            "suggested_path_slug": "execute",
            "errors": [f"Suggest endpoint failed: {e}"],
        }


def format_task_description(state: PlannerState) -> dict[str, Any]:
    user_prompt = state.get("user_prompt") or ""
    services = state.get("services") or []
    workflow_steps = state.get("workflow_steps") or []
    parameters = state.get("parameters") or []
    suggested_endpoints = state.get("suggested_endpoints") or []
    method = state.get("suggested_http_method") or "POST"
    path_slug = state.get("suggested_path_slug") or "execute"
    parts = [f"Task: {user_prompt}"]
    if workflow_steps:
        parts.append("Workflow steps (execute in order):")
        for s in workflow_steps:
            idx = s.get("step_index", 0)
            action = s.get("action", "")
            hint = s.get("service_hint", "")
            desc = s.get("description", "")
            line = f"  {idx}. {action}"
            if hint:
                line += f" ({hint})"
            if desc:
                line += f" — {desc}"
            parts.append(line)
    if suggested_endpoints:
        for i, ep in enumerate(suggested_endpoints):
            m = ep.get("method", "POST")
            slug = ep.get("path_slug", "execute")
            summary = ep.get("summary", "")
            parts.append(f"Endpoint {i}: {m} /{slug}" + (f" — {summary}" if summary else ""))
    else:
        parts.append(f"Suggested endpoint: {method} /{path_slug}")
    if services:
        parts.append(f"Services: {', '.join(services)}")
    if parameters:
        param_lines = []
        for p in parameters:
            loc = p.get("location", "body")
            how = p.get("how_used", "")
            ei = p.get("endpoint_index", 0)
            param_lines.append(f"- {p.get('name', '')} ({p.get('type', 'str')}, {loc}, endpoint {ei}): {how or p.get('description', '')}")
        parts.append("Parameters:\n" + "\n".join(param_lines))
    return {"task_description": "\n".join(parts)}


def build_planner_graph() -> StateGraph:
    builder: StateGraph = StateGraph(PlannerState)
    builder.add_node("validate_task", validate_task)
    builder.add_node("extract_services", extract_services)
    builder.add_node("extract_workflow_steps", extract_workflow_steps)
    builder.add_node("extract_parameters", extract_parameters)
    builder.add_node("suggest_endpoint", suggest_endpoint)
    builder.add_node("format_task_description", format_task_description)
    builder.add_edge(START, "validate_task")
    builder.add_edge("validate_task", "extract_services")
    builder.add_edge("extract_services", "extract_workflow_steps")
    builder.add_edge("extract_workflow_steps", "extract_parameters")
    builder.add_edge("extract_parameters", "suggest_endpoint")
    builder.add_edge("suggest_endpoint", "format_task_description")
    builder.add_edge("format_task_description", END)
    return builder


def create_planner() -> Any:
    return build_planner_graph().compile()


def run_planner(user_prompt: str) -> dict[str, Any]:
    graph = create_planner()
    initial: PlannerState = {"user_prompt": user_prompt}
    return graph.invoke(initial)


planner = create_planner()
