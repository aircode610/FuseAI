"""
Step-by-step prompts for the planner agent.

Used by planner nodes to validate the task and extract services, parameters,
and endpoint hints. The LLM returns structured output (Pydantic schemas) via
LangChain—no JSON instructions needed in the prompts.
"""

# ---------------------------------------------------------------------------
# Step 1: Validate the task
# ---------------------------------------------------------------------------

VALIDATE_TASK_SYSTEM = """You are a validator for workflow task descriptions. Decide if the user's input describes a valid, actionable workflow task that could be implemented as an API agent (e.g. "get X from service A and send to service B", "fetch Y by Z", "update W").

- valid: true if the input is a coherent workflow task; false if it is empty, gibberish, or not a task.
- reason: one short sentence explaining why (e.g. "Clear task involving Trello and Slack" or "Input is empty").
"""

VALIDATE_TASK_USER = """Validate this user input as a workflow task.

User input:
{user_prompt}
"""


# ---------------------------------------------------------------------------
# Step 2: Extract services (apps/integrations)
# ---------------------------------------------------------------------------

EXTRACT_SERVICES_SYSTEM = """You are an analyst that identifies external services or apps mentioned in a workflow task (e.g. Trello, Slack, GitHub, Gmail, Salesforce, Asana, Discord, Notion, Jira). These will be used for API integration (e.g. via Zapier).

List distinct service/app names mentioned in the task. Use standard names (e.g. "Trello", "Slack", "Google Sheets"). If none are clearly mentioned, return an empty list.
"""

EXTRACT_SERVICES_USER = """From the following workflow task, list every external service or app that is mentioned or implied.

Workflow task:
{user_prompt}
"""


# ---------------------------------------------------------------------------
# Step 3: Extract parameters and how they are used
# ---------------------------------------------------------------------------

EXTRACT_PARAMETERS_SYSTEM = """You are an API designer. Given a workflow task and the list of services involved, list ONLY the parameters that are explicitly required by the task—i.e. mentioned or clearly implied (e.g. "for a person" → person identifier, "send to Slack" → Slack recipient).

Do NOT add:
- Optional filters (board_filter, card_status, date_range, etc.)
- Format or preference options (summary_format, output_format, etc.)
- Any parameter that is not directly stated or clearly implied by the task.

For each parameter: name (snake_case), type (str, int, or bool), description, required (true), location (path, query, or body), and how_used (one sentence).

- location "path": for resource identifiers in URLs (e.g. GET /contacts/{email}, PUT /tickets/{ticket_id}).
- location "query": for required query args (use sparingly; prefer body for POST).
- location "body": for main payload (POST/PUT body).
- how_used: concise, e.g. "Person whose Trello cards to fetch", "Slack channel or user ID to send the summary to".

Keep the list minimal: only parameters the user would have to supply to run the described workflow.
"""

EXTRACT_PARAMETERS_USER = """Workflow task:
{user_prompt}

Services involved: {services}

List ONLY the parameters that are explicitly required by this task (mentioned or clearly implied). Do not add optional filters or format options. For each parameter include name (snake_case), type, description, required=true, location (path/query/body), and how_used.
"""


# ---------------------------------------------------------------------------
# Step 4: Suggest HTTP method and path slug
# ---------------------------------------------------------------------------

SUGGEST_ENDPOINT_SYSTEM = """You suggest REST endpoint details for a workflow task. Given the task and the services, suggest the HTTP method and a short path slug.

- method: GET for read/fetch/list, POST for create/send/sync/summarize, PUT for update, DELETE for remove/cleanup.
- path_slug: short, hyphenated, e.g. summarize-cards, contacts, sync-issues, tickets, cards/cleanup. No leading slash.
"""

SUGGEST_ENDPOINT_USER = """Workflow task:
{user_prompt}

Services: {services}

Suggest the HTTP method and path slug for the API endpoint.
"""


# ---------------------------------------------------------------------------
# Helpers: format prompts with state
# ---------------------------------------------------------------------------

def format_validate_task(user_prompt: str) -> tuple[str, str]:
    """Return (system, user) for validate_task step."""
    return VALIDATE_TASK_SYSTEM, VALIDATE_TASK_USER.format(user_prompt=user_prompt or "")


def format_extract_services(user_prompt: str) -> tuple[str, str]:
    """Return (system, user) for extract_services step."""
    return EXTRACT_SERVICES_SYSTEM, EXTRACT_SERVICES_USER.format(user_prompt=user_prompt or "")


def format_extract_parameters(user_prompt: str, services: list[str]) -> tuple[str, str]:
    """Return (system, user) for extract_parameters step."""
    services_str = ", ".join(services) if services else "none"
    return (
        EXTRACT_PARAMETERS_SYSTEM,
        EXTRACT_PARAMETERS_USER.format(user_prompt=user_prompt or "", services=services_str),
    )


def format_suggest_endpoint(user_prompt: str, services: list[str]) -> tuple[str, str]:
    """Return (system, user) for suggest_endpoint step."""
    services_str = ", ".join(services) if services else "none"
    return (
        SUGGEST_ENDPOINT_SYSTEM,
        SUGGEST_ENDPOINT_USER.format(user_prompt=user_prompt or "", services=services_str),
    )
