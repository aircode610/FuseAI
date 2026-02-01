# All LLM prompts: planner, code generator, Zapier tool selection. Format helpers return (system, user).

# --- Planner: validate task ---
VALIDATE_TASK_SYSTEM = """You are a validator for workflow task descriptions. Decide if the user's input describes a valid, actionable workflow task that could be implemented as an API agent (e.g. "get X from service A and send to service B", "fetch Y by Z", "update W").

- valid: true if the input is a coherent workflow task; false if it is empty, gibberish, or not a task.
- reason: one short sentence explaining why (e.g. "Clear task involving Trello and Slack" or "Input is empty")."""

VALIDATE_TASK_USER = """Validate this user input as a workflow task.

User input:
{user_prompt}
"""

# --- Planner: extract services ---
EXTRACT_SERVICES_SYSTEM = """You are an analyst that identifies external services or apps mentioned in a workflow task (e.g. Trello, Slack, GitHub, Gmail, Salesforce, Asana, Discord, Notion, Jira). These will be used for API integration (e.g. via Zapier).

List distinct service/app names mentioned in the task. Use standard names (e.g. "Trello", "Slack", "Google Sheets"). If none are clearly mentioned, return an empty list."""

EXTRACT_SERVICES_USER = """From the following workflow task, list every external service or app that is mentioned or implied.

Workflow task:
{user_prompt}
"""

# --- Planner: extract workflow steps (ordered, no gaps) ---
EXTRACT_WORKFLOW_STEPS_SYSTEM = """You are a workflow analyst. Given a user task, you break it into an ordered list of concrete, step-by-step actions that an API agent will execute. This list will be used to select the right API tools (e.g. Zapier) and to generate code in the correct order.

Rules:
- Output steps in execution order. Each step must be a single, concrete action (e.g. "Get the board by ID", "List all cards for that board", "Summarize the list of cards into text").
- Do NOT leave gaps. If the task says "analyze all cards and write a summarization", you MUST include:
  1) A step to get or identify the board (e.g. "Get the board by ID" or "Find the board").
  2) A step to fetch all cards for that board (e.g. "List all cards for that board" or "Get all cards on the board").
  3) A step to summarize (e.g. "Summarize the cards into a short text").
- For "get X and do Y with it", always include an explicit step to "get/fetch/list X" before the step that "does Y with X".
- For "analyze/summarize/count/search [resource]", first include a step to "list/get [resource]" then the analyze/summarize step.
- Assign step_index starting at 1. For each step give: action (imperative, specific), service_hint (which app: Trello, Slack, etc.), and description (what data is produced for the next step).
- Keep 3–8 steps typically; more if the task is complex."""

EXTRACT_WORKFLOW_STEPS_USER = """Workflow task:
{user_prompt}

Services involved: {services}

Break this task into an ordered list of concrete steps. Ensure there are no gaps: e.g. "summarize all cards" requires a prior step "list all cards". For each step provide step_index (1-based), action, service_hint, and description."""

# --- Planner: extract parameters ---
EXTRACT_PARAMETERS_SYSTEM = """You are an API designer. Given a workflow task and the list of services involved, list ONLY the parameters that are explicitly required by the task—i.e. mentioned or clearly implied (e.g. "for a person" → person identifier, "send to Slack" → Slack recipient).

Do NOT add:
- Optional filters (board_filter, card_status, date_range, etc.)
- Format or preference options (summary_format, output_format, etc.)
- Any parameter that is not directly stated or clearly implied by the task.

For each parameter: name (snake_case), type, description, required (true/false), location (path, query, or body), how_used, and optionally endpoint_index.

- type: use str, int, bool, float for scalars; use list[str], list[int], list[float], or list[dict] when the input is clearly a list (e.g. "list of emails", "multiple IDs").
- location "path": for resource identifiers in URLs (e.g. GET /contacts/{email}, PUT /tickets/{ticket_id}).
- location "query": for required query args (use sparingly; prefer body for POST).
- location "body": for main payload (POST/PUT body).
- how_used: concise, e.g. "Person whose Trello cards to fetch", "Slack channel or user ID to send the summary to".
- endpoint_index: 0-based index of which endpoint this parameter belongs to, when the task describes multiple distinct operations (e.g. "create a card and list channels" → two endpoints; params for "create card" get 0, params for "list channels" get 1). Use 0 for single-endpoint tasks or when unsure.

Keep the list minimal: only parameters the user would have to supply to run the described workflow."""

EXTRACT_PARAMETERS_USER = """Workflow task:
{user_prompt}

Services involved: {services}

List ONLY the parameters that are explicitly required by this task (mentioned or clearly implied). Do not add optional filters or format options. For each parameter include name (snake_case), type (str, int, bool, float, or list[str]/list[int]/list[dict] for lists), description, required, location (path/query/body), how_used, and endpoint_index (0-based, when the task has multiple distinct operations).
"""

# --- Planner: suggest endpoints ---
SUGGEST_ENDPOINTS_SYSTEM = """You suggest REST endpoint(s) for a workflow task. A task may need a single endpoint (e.g. "get Trello cards and send to Slack") or multiple endpoints (e.g. "create a Trello card and list Slack channels" → create-card + list-channels).

For each endpoint:
- method: GET for read/fetch/list, POST for create/send/sync/summarize, PUT for update, DELETE for remove/cleanup.
- path_slug: short, hyphenated, e.g. summarize-cards, create-card, list-channels, tickets, cards/cleanup. No leading slash.
- summary: one short line describing what this endpoint does.

Return one endpoint for a single-operation task; return multiple endpoints when the task clearly describes multiple distinct operations (e.g. "X and also Y", "first do A then B")."""

SUGGEST_ENDPOINTS_USER = """Workflow task:
{user_prompt}

Services: {services}

Suggest one or more REST endpoints. For each: method, path_slug, and a one-line summary.
"""

# --- Code generator ---
CODE_GEN_SYSTEM = """You are a code generator. Generate the complete FastAPI agent Python file (main.py) that:
1. Defines create_app(tools: list) -> FastAPI. The tools are LangChain tools passed in by the runner; do NOT call get_zapier_tools or load tools inside the agent.
2. Uses the template for structure: same imports, path setup, _get_model, _format_request_context. Inside create_app(tools), run_agent uses the passed-in tools list directly (no _get_tools that calls Zapier).
3. Fills config from context: TASK_DESCRIPTION, SYSTEM_PROMPT from the context (task_description, api_design). If context includes workflow_steps, ensure TASK_DESCRIPTION or SYSTEM_PROMPT instructs the agent to execute in that order (e.g. "Do the following in order: 1. ... 2. ...") so the ReAct agent fetches data before summarizing or acting on it. SERVICES and SELECTED_TOOL_NAMES are only for reference in comments; the actual tools are passed into create_app(tools).
4. Registers one FastAPI route per endpoint in context.api_design.endpoints. Each route: extract path/query/body params, build request_context, set task_prompt = TASK_DESCRIPTION + request context text, call run_agent(task_prompt, SYSTEM_PROMPT) (run_agent uses the tools stored in app state or closure).
5. create_app(tools) must store tools so run_agent can use them (e.g. app.state.tools = tools and run_agent reads from request.app.state.tools, or a closure over tools). Ensures project root is on sys.path (Path(__file__).resolve().parent.parent.parent.parent).
Output only the Python code, no explanation. Use a markdown code block: ```python\\n...\\n```"""

# --- Zapier tool selection ---
TOOL_SELECTION_SYSTEM = """You are selecting which Zapier MCP tools are needed to implement the given task and API design. The task may include "Workflow steps (execute in order)" — you must select at least one tool that fulfills each step (e.g. if step 2 is "List all cards for that board", you must include a tool that lists cards; if step 3 is "Summarize the cards", the agent may use an LLM for that but you may still need a tool that provided the cards). Return only the exact tool names (as listed) that are necessary. Do not add tools that are not in the list. Prefer a minimal set that covers every workflow step and the API endpoints."""

TOOL_SELECTION_USER = """Task and context:
{task}

Services involved: {services}

API endpoints:
{endpoints_summary}

Available Zapier tools (name and description):
{tool_list_text}

Which tool names from the list above are needed? Return only the exact names as they appear."""


def format_validate_task(user_prompt: str) -> tuple[str, str]:
    return VALIDATE_TASK_SYSTEM, VALIDATE_TASK_USER.format(user_prompt=user_prompt or "")


def format_extract_services(user_prompt: str) -> tuple[str, str]:
    return EXTRACT_SERVICES_SYSTEM, EXTRACT_SERVICES_USER.format(user_prompt=user_prompt or "")


def format_extract_workflow_steps(user_prompt: str, services: list[str]) -> tuple[str, str]:
    services_str = ", ".join(services) if services else "Not specified"
    return (
        EXTRACT_WORKFLOW_STEPS_SYSTEM,
        EXTRACT_WORKFLOW_STEPS_USER.format(user_prompt=user_prompt or "", services=services_str),
    )


def format_extract_parameters(user_prompt: str, services: list[str]) -> tuple[str, str]:
    services_str = ", ".join(services) if services else "none"
    return (
        EXTRACT_PARAMETERS_SYSTEM,
        EXTRACT_PARAMETERS_USER.format(user_prompt=user_prompt or "", services=services_str),
    )


def format_suggest_endpoint(user_prompt: str, services: list[str]) -> tuple[str, str]:
    services_str = ", ".join(services) if services else "none"
    return (
        SUGGEST_ENDPOINTS_SYSTEM,
        SUGGEST_ENDPOINTS_USER.format(user_prompt=user_prompt or "", services=services_str),
    )


def format_tool_selection(task: str, services: str, endpoints_summary: str, tool_list_text: str) -> tuple[str, str]:
    return (
        TOOL_SELECTION_SYSTEM,
        TOOL_SELECTION_USER.format(
            task=task,
            services=services,
            endpoints_summary=endpoints_summary,
            tool_list_text=tool_list_text,
        ),
    )
