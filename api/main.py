"""
FastAPI app: design agent endpoint.

POST /design — Run the unified design agent (planner → API designer → Zapier tool selection with LLM)
and return context_for_coding_agent (api_design + selected_zapier_tools) for the coding agent to build
an agent from.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from core.agent import run_design_agent_async

app = FastAPI(
    title="FuseAI Design API",
    description="Unified design agent: plan → API design → Zapier tool selection. Output is context for the coding agent.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------


class DesignRequest(BaseModel):
    """Request body for POST /design."""

    user_prompt: str = Field(
        ...,
        description="Task description in plain language (e.g. 'Analyze Trello board cards and post health report to Slack').",
    )


class DesignResponse(BaseModel):
    """Response: context for the coding agent."""

    success: bool = Field(description="Whether the design pipeline completed without error.")
    context_for_coding_agent: dict[str, Any] | None = Field(
        default=None,
        description="API design + selected Zapier tools (serialized) for the coding agent to build an agent from.",
    )
    error: str | None = Field(default=None, description="Error message if success is False.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.post(
    "/design",
    response_model=DesignResponse,
    summary="Run design agent",
    description="Runs planner → API designer → Zapier MCP tool selection (LLM). Returns context_for_coding_agent (api_design + selected_zapier_tools) for the coding agent.",
)
async def design(body: DesignRequest) -> DesignResponse:
    """
    Run the unified design agent on the given task prompt.

    Context flows: planner → API designer → Zapier tools loaded → LLM selects tools → context saved.
    Response includes api_design (endpoints, parameters) and selected_zapier_tools (name, description, args_schema)
    for the coding agent to build an agent from.
    """
    try:
        state = await run_design_agent_async(body.user_prompt)
    except Exception as e:
        return DesignResponse(
            success=False,
            context_for_coding_agent=None,
            error=str(e),
        )

    context_for_coding_agent = state.get("context_for_coding_agent")
    planner_context = state.get("planner_context") or {}
    if not planner_context.get("valid", True):
        return DesignResponse(
            success=False,
            context_for_coding_agent=context_for_coding_agent,
            error=planner_context.get("validation_reason") or "Task validation failed.",
        )

    return DesignResponse(
        success=True,
        context_for_coding_agent=context_for_coding_agent,
        error=None,
    )


# ---------------------------------------------------------------------------
# Run with: uvicorn api.main:app --reload
# ---------------------------------------------------------------------------
