# Pydantic models and TypedDict states used by planner, api_designer, agent, zapier_mapper.

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field

ParamLocation = Literal["path", "query", "body"]

# --- Planner: structured LLM outputs ---
class ValidateOutput(BaseModel):
    valid: bool = Field(description="True if the input is a coherent workflow task")
    reason: str = Field(description="One short sentence explaining why")


class ServicesOutput(BaseModel):
    services: list[str] = Field(default_factory=list, description="Distinct service/app names (e.g. Trello, Slack)")


class ParameterItem(BaseModel):
    name: str = Field(description="snake_case parameter name")
    type: str = Field(default="str", description="str, int, bool, float, or list[str]/list[int]/list[dict]")
    description: str = Field(default="", description="What this parameter is for")
    required: bool = Field(default=True, description="Whether the parameter is required")
    location: ParamLocation = Field(default="body", description="path, query, or body")
    how_used: str = Field(default="", description="How this parameter is used in the task")
    endpoint_index: int = Field(default=0, description="0-based endpoint index for multi-endpoint tasks")


class ParametersOutput(BaseModel):
    parameters: list[ParameterItem] = Field(default_factory=list, description="API parameters")


class EndpointHint(BaseModel):
    method: str = Field(default="POST", description="GET, POST, PUT, DELETE, or PATCH")
    path_slug: str = Field(default="execute", description="Short hyphenated slug, no leading slash")
    summary: str = Field(default="", description="One-line summary of what this endpoint does")


class EndpointsOutput(BaseModel):
    endpoints: list[EndpointHint] = Field(default_factory=list, description="One or more REST endpoints")


# --- Planner: LangGraph state ---
class ParameterSpec(TypedDict, total=False):
    name: str
    type: str
    description: str
    required: bool
    location: ParamLocation
    how_used: str
    endpoint_index: int


class ValidationResult(TypedDict, total=False):
    valid: bool
    reason: str


class PlannerState(TypedDict, total=False):
    user_prompt: str
    validation_result: ValidationResult
    services: list[str]
    parameters: list[ParameterSpec]
    suggested_http_method: str
    suggested_path_slug: str
    suggested_endpoints: list[dict[str, Any]]
    task_description: str
    errors: Annotated[list[str], lambda a, b: (a or []) + (b or [])]


# --- API designer: code-gen ready schemas ---
class ParameterDesign(BaseModel):
    name: str = Field(description="snake_case name for FastAPI")
    type: str = Field(default="str", description="Python/FastAPI type")
    description: str = Field(default="", description="For OpenAPI/docs")
    required: bool = Field(default=True, description="Whether the parameter is required")
    location: ParamLocation = Field(default="body", description="path, query, or body")


class APIEndpointDesign(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(default="POST")
    path: str = Field(default="/execute", description="URL path, no trailing slash")
    operation_id: str = Field(default="execute", description="OpenAPI operation_id")
    summary: str = Field(default="Execute the workflow")
    path_parameters: list[ParameterDesign] = Field(default_factory=list)
    query_parameters: list[ParameterDesign] = Field(default_factory=list)
    body_parameters: list[ParameterDesign] = Field(default_factory=list)
    response_description: str = Field(default="Result of the operation")


class APIDesign(BaseModel):
    endpoints: list[APIEndpointDesign] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    task_description: str = Field(default="")


# --- Design agent: LangGraph state ---
class DesignAgentState(TypedDict, total=False):
    user_prompt: str
    planner_context: dict[str, Any]
    available_zapier_tools: list[Any]
    selected_tool_names: list[str]
    selected_zapier_tools: list[dict[str, Any]]
    selected_tools_objects: list[Any]
    context_for_coding_agent: dict[str, Any]


# --- Zapier tool selection: structured LLM output ---
class SelectedToolsOutput(BaseModel):
    tool_names: list[str] = Field(
        description="Exact names of the Zapier tools to use (subset of the available list). Use only the tool name as shown."
    )
