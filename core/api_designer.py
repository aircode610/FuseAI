# API designer: planner state → APIDesign (endpoints) for code generator.

from __future__ import annotations

from typing import Any

from core.models import APIDesign, APIEndpointDesign, ParameterDesign


def _normalize_type(t: str) -> str:
    if not t:
        return "str"
    raw = (t or "").strip()
    t = raw.lower()
    if t in ("str", "string"):
        return "str"
    if t in ("int", "integer"):
        return "int"
    if t in ("bool", "boolean"):
        return "bool"
    if t in ("float", "number"):
        return "float"
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
    if not slug:
        return "execute"
    return slug.strip().strip("/").replace("-", "_").replace(" ", "_") or "execute"


def _build_one_endpoint(
    method: str,
    path_slug: str,
    endpoint_summary: str,
    raw_params_for_this_endpoint: list[dict[str, Any]],
) -> APIEndpointDesign:
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
    raw_params: list[dict[str, Any]] = planner_state.get("parameters") or []
    services: list[str] = list(planner_state.get("services") or [])
    task_description: str = (planner_state.get("task_description") or "").strip()
    suggested_endpoints: list[dict[str, Any]] = planner_state.get("suggested_endpoints") or []
    if not suggested_endpoints:
        method = (planner_state.get("suggested_http_method") or "POST").upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            method = "POST"
        path_slug = (planner_state.get("suggested_path_slug") or "execute").strip().strip("/").replace(" ", "-") or "execute"
        summary = "Execute the workflow"
        if task_description:
            first_line = task_description.split("\n")[0].strip()
            summary = first_line[5:].strip()[:120] if first_line.lower().startswith("task:") else first_line[:120] or summary
        suggested_endpoints = [{"method": method, "path_slug": path_slug, "summary": summary}]
    endpoints: list[APIEndpointDesign] = []
    for i, ep in enumerate(suggested_endpoints):
        method = (ep.get("method") or "POST").upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            method = "POST"
        path_slug = (ep.get("path_slug") or "execute").strip().strip("/").replace(" ", "-") or "execute"
        summary = (ep.get("summary") or "").strip() or "Execute the workflow"
        params_for_i = [p for p in raw_params if p.get("endpoint_index", 0) == i]
        endpoints.append(_build_one_endpoint(method, path_slug, summary, params_for_i))
    return APIDesign(endpoints=endpoints, services=services, task_description=task_description)


def run_api_designer(planner_state: dict[str, Any]) -> APIDesign:
    return design_from_planner_state(planner_state)
