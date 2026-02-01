# Re-export prompts and format helpers for backward compatibility.
from core.prompts import (
    EXTRACT_PARAMETERS_SYSTEM,
    EXTRACT_PARAMETERS_USER,
    EXTRACT_SERVICES_SYSTEM,
    EXTRACT_SERVICES_USER,
    EXTRACT_WORKFLOW_STEPS_SYSTEM,
    EXTRACT_WORKFLOW_STEPS_USER,
    SUGGEST_ENDPOINTS_SYSTEM,
    SUGGEST_ENDPOINTS_USER,
    VALIDATE_TASK_SYSTEM,
    VALIDATE_TASK_USER,
    format_extract_parameters,
    format_extract_services,
    format_extract_workflow_steps,
    format_suggest_endpoint,
    format_validate_task,
)
