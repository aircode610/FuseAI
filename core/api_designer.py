"""
API Designer: turns planner output into a single-endpoint API design.

Consumes PlannerState (services, parameters, suggested_http_method,
suggested_path_slug, task_description) and produces an APIEndpointDesign
in a format ready for the code generator to turn into FastAPI code.
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
    type: Literal["str", "int", "bool", "float"] = Field(
        default="str",
        description="Python/FastAPI type",
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
    # Optional: keep services for code gen (e.g. for task prompt or docs)
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

def _normalize_type(t: str) -> Literal["str", "int", "bool", "float"]:
    """Map planner type string to allowed FastAPI type."""
    if not t:
        return "str"
    t = (t or "").strip().lower()
    if t in ("str", "string"):
        return "str"
    if t in ("int", "integer"):
        return "int"
    if t in ("bool", "boolean"):
        return "bool"
    if t in ("float", "number"):
        return "float"
    return "str"


def _slug_to_operation_id(slug: str) -> str:
    """Convert path slug to operation_id (e.g. get-cards -> get_cards)."""
    if not slug:
        return "execute"
    return slug.strip().strip("/").replace("-", "_").replace(" ", "_") or "execute"


def design_from_planner_state(planner_state: dict[str, Any]) -> APIEndpointDesign:
    """
    Build an API endpoint design from planner output.

    - Uses suggested_http_method and suggested_path_slug.
    - Splits parameters by location into path_parameters, query_parameters, body_parameters.
    - Builds path string with path params (e.g. /cards/{board_id}).
    - Sets operation_id and summary from path_slug and task_description.
    """
    method = (planner_state.get("suggested_http_method") or "POST").upper()
    if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        method = "POST"

    path_slug = (planner_state.get("suggested_path_slug") or "execute").strip().strip("/").replace(" ", "-") or "execute"
    raw_params: list[dict[str, Any]] = planner_state.get("parameters") or []
    services: list[str] = list(planner_state.get("services") or [])
    task_description: str = (planner_state.get("task_description") or "").strip()

    # Split by location and build ParameterDesign list
    path_params: list[ParameterDesign] = []
    query_params: list[ParameterDesign] = []
    body_params: list[ParameterDesign] = []

    for p in raw_params:
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

    # Build path: /slug or /slug/{param1}/{param2}
    path_segments = [path_slug]
    for pp in path_params:
        path_segments.append(f"{{{pp.name}}}")
    path = "/" + "/".join(path_segments)

    operation_id = _slug_to_operation_id(path_slug)
    # First line of task description as summary, or derived from slug
    summary = "Execute the workflow"
    if task_description:
        first_line = task_description.split("\n")[0].strip()
        if first_line.lower().startswith("task:"):
            summary = first_line[5:].strip()[:120] or summary
        else:
            summary = first_line[:120] or summary

    response_description = "Result of the operation"
    if task_description:
        response_description = f"Result for: {task_description.split(chr(10))[0].strip()[:80]}"

    return APIEndpointDesign(
        method=method,
        path=path,
        operation_id=operation_id,
        summary=summary,
        path_parameters=path_params,
        query_parameters=query_params,
        body_parameters=body_params,
        response_description=response_description,
        services=services,
        task_description=task_description,
    )


def run_api_designer(planner_state: dict[str, Any]) -> APIEndpointDesign:
    """
    Run the API designer on planner output.

    This is the main entry point for the pipeline: planner state in,
    APIEndpointDesign out (for the code generator).
    """
    return design_from_planner_state(planner_state)
