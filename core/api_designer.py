"""
API Designer: turns planner output into an API design (one or more endpoints).

Consumes PlannerState (services, parameters, suggested_endpoints or
suggested_http_method/suggested_path_slug, task_description) and produces
an APIDesign in a format ready for the code generator to turn into FastAPI code.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# API design schema (code-generator / FastAPI ready)
# ---------------------------------------------------------------------------

ParamLocation = Literal["path", "query", "body"]

class ParameterDesign(BaseModel):
    """One parameter in the API design (path, query, or body)."""

    name: str = Field(description="snake_case name for FastAPI")
    type: str = Field(
        default="str",
        description="Python/FastAPI type: str, int, bool, float, or list[str], list[int], list[dict], etc.",
    )
    description: str = Field(default="", description="For OpenAPI/docs")
    required: bool = Field(default=True, description="Whether the parameter is required")
    location: ParamLocation = Field(
        default="body",
        description="path, query, or body",
    )


class APIEndpointDesign(BaseModel):
    """
    Full design for one REST endpoint, ready for code generator.

    The code generator will use this to:
    - Define the route (method + path with path params)
    - Add path/query/body parameters with correct FastAPI types
    - Generate a Pydantic request body model from body_parameters
    - Set operation_id, summary, and response_description for OpenAPI
    """

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(
        default="POST",
        description="HTTP method for the endpoint",
    )
    path: str = Field(
        default="/execute",
        description="URL path, e.g. /execute or /cards/{board_id} (no trailing slash)",
    )
    operation_id: str = Field(
        default="execute",
        description="OpenAPI operation_id (e.g. execute_task, get_cards)",
    )
    summary: str = Field(
        default="Execute the workflow",
        description="Short one-line summary for OpenAPI",
    )
    path_parameters: list[ParameterDesign] = Field(
        default_factory=list,
        description="Parameters that appear in the path (e.g. {board_id})",
    )
    query_parameters: list[ParameterDesign] = Field(
        default_factory=list,
        description="Query string parameters",
    )
    body_parameters: list[ParameterDesign] = Field(
        default_factory=list,
        description="Request body fields (code gen will create a Pydantic model)",
    )
    response_description: str = Field(
        default="Result of the operation",
        description="Description for the response in OpenAPI",
    )


class APIDesign(BaseModel):
    """
    Full API design: one or more endpoints, ready for code generator.

    The code generator will iterate over endpoints and generate one route per
    endpoint, with path/query/body params and request body models as needed.
    """

    endpoints: list[APIEndpointDesign] = Field(
        default_factory=list,
        description="One or more REST endpoints to generate",
    )
    services: list[str] = Field(
        default_factory=list,
        description="Services involved (e.g. Trello, Slack) for context",
    )
    task_description: str = Field(
        default="",
        description="Full task description for code gen / agent prompt",
    )


# ---------------------------------------------------------------------------
# Design from planner state (deterministic, no LLM)
# ---------------------------------------------------------------------------

def _normalize_type(t: str) -> str:
    """Map planner type string to FastAPI/Pydantic type string (scalars and lists)."""
    if not t:
        return "str"
    raw = (t or "").strip()
    t = raw.lower()
    # Scalars
    if t in ("str", "string"):
        return "str"
    if t in ("int", "integer"):
        return "int"
    if t in ("bool", "boolean"):
        return "bool"
    if t in ("float", "number"):
        return "float"
    # List types (exact or normalized)
    if t.startswith("list[") and "]" in t:
        inner = t[5:t.index("]")].strip().lower()
        if inner in ("str", "string"):
            return "list[str]"
        if inner in ("int", "integer"):
            return "list[int]"
        if inner in ("float", "number"):
            return "list[float]"
        if inner in ("bool", "boolean"):
            return "list[bool]"
        if inner in ("dict", "object"):
            return "list[dict]"
        return "list[str]"
    if t in ("list", "array"):
        return "list[str]"
    return "str"


def _slug_to_operation_id(slug: str) -> str:
    """Convert path slug to operation_id (e.g. get-cards -> get_cards)."""
    if not slug:
        return "execute"
    return slug.strip().strip("/").replace("-", "_").replace(" ", "_") or "execute"


def _build_one_endpoint(
    method: str,
    path_slug: str,
    endpoint_summary: str,
    raw_params_for_this_endpoint: list[dict[str, Any]],
) -> APIEndpointDesign:
    """Build a single APIEndpointDesign from method, slug, summary, and params."""
    path_params: list[ParameterDesign] = []
    query_params: list[ParameterDesign] = []
    body_params: list[ParameterDesign] = []

    for p in raw_params_for_this_endpoint:
        name = (p.get("name") or "param").strip()
        if not name:
            continue
        loc = (p.get("location") or "body").lower()
        if loc not in ("path", "query", "body"):
            loc = "body"
        param = ParameterDesign(
            name=name,
            type=_normalize_type(p.get("type") or "str"),
            description=(p.get("description") or p.get("how_used") or "").strip(),
            required=bool(p.get("required", True)),
            location=loc,
        )
        if loc == "path":
            path_params.append(param)
        elif loc == "query":
            query_params.append(param)
        else:
            body_params.append(param)

    path_segments = [path_slug]
    for pp in path_params:
        path_segments.append(f"{{{pp.name}}}")
    path = "/" + "/".join(path_segments)

    operation_id = _slug_to_operation_id(path_slug)
    summary = endpoint_summary[:120] if endpoint_summary else "Execute the workflow"
    response_description = f"Result for: {summary[:80]}" if summary else "Result of the operation"

    return APIEndpointDesign(
        method=method,
        path=path,
        operation_id=operation_id,
        summary=summary,
        path_parameters=path_params,
        query_parameters=query_params,
        body_parameters=body_params,
        response_description=response_description,
    )


def design_from_planner_state(planner_state: dict[str, Any]) -> APIDesign:
    """
    Build an API design (one or more endpoints) from planner output.

    - If suggested_endpoints is present: one endpoint per entry; parameters are
      assigned by endpoint_index (params with endpoint_index == i go to endpoint i).
    - If only suggested_http_method/suggested_path_slug: single endpoint (backward compat).
    - Parameter types support scalars and lists (str, int, list[str], list[int], etc.).
    """
    raw_params: list[dict[str, Any]] = planner_state.get("parameters") or []
    services: list[str] = list(planner_state.get("services") or [])
    task_description: str = (planner_state.get("task_description") or "").strip()
    suggested_endpoints: list[dict[str, Any]] = planner_state.get("suggested_endpoints") or []

    if not suggested_endpoints:
        # Backward compat: single endpoint from suggested_http_method / suggested_path_slug
        method = (planner_state.get("suggested_http_method") or "POST").upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            method = "POST"
        path_slug = (planner_state.get("suggested_path_slug") or "execute").strip().strip("/").replace(" ", "-") or "execute"
        summary = "Execute the workflow"
        if task_description:
            first_line = task_description.split("\n")[0].strip()
            if first_line.lower().startswith("task:"):
                summary = first_line[5:].strip()[:120] or summary
            else:
                summary = first_line[:120] or summary
        suggested_endpoints = [{"method": method, "path_slug": path_slug, "summary": summary}]

    endpoints: list[APIEndpointDesign] = []
    for i, ep in enumerate(suggested_endpoints):
        method = (ep.get("method") or "POST").upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            method = "POST"
        path_slug = (ep.get("path_slug") or "execute").strip().strip("/").replace(" ", "-") or "execute"
        summary = (ep.get("summary") or "").strip() or "Execute the workflow"
        params_for_i = [p for p in raw_params if p.get("endpoint_index", 0) == i]
        endpoints.append(
            _build_one_endpoint(
                method=method,
                path_slug=path_slug,
                endpoint_summary=summary,
                raw_params_for_this_endpoint=params_for_i,
            )
        )

    return APIDesign(
        endpoints=endpoints,
        services=services,
        task_description=task_description,
    )


def run_api_designer(planner_state: dict[str, Any]) -> APIDesign:
    """
    Run the API designer on planner output.

    This is the main entry point for the pipeline: planner state in,
    APIDesign out (one or more endpoints for the code generator).
    """
    return design_from_planner_state(planner_state)
