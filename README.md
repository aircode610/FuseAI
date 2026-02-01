# FuseAI

An AI-powered agent builder that lets users describe a workflow in plain English and automatically generates, deploys, and monitors custom API agents.

## Overview

FuseAI analyzes natural language requests, designs REST APIs, generates FastAPI code from a single template using Zapier MCP for integrations, and deploys running agents with monitoring, error handling (using web search), and a testing playground.

## Project Structure

### `generator/core/` - Core Generation Pipeline

**`planner.py`** - Analyzes user prompts and extracts requirements. Should implement: prompt parsing, service extraction (Trello, Slack, etc.), parameter inference based on services, and task description formatting.

**`api_designer.py`** - Designs REST API structure for generated agents. Should implement: endpoint generation (GET/POST/PUT/DELETE/PATCH) based on task requirements, parameter extraction and typing, path parameter vs body parameter decisions, authentication setup, and API documentation generation.

**`code_generator.py`** - Generates FastAPI code using the agent template. Should implement: template loading, Claude prompt generation for the agent's task, template variable filling, configuration file creation, and requirements.txt generation.

**`deployer.py`** - Deploys agents to runtime environment. Should implement: agent directory creation, file writing (main.py, config.json), dependency installation, FastAPI server startup, port management, API key generation, and monitoring setup.

### `generator/templates/` - Code Template

**`agent_template.py`** - Single FastAPI template for all agents. Should include: FastAPI app structure with flexible endpoint generation (GET/POST/PUT/DELETE/PATCH), Claude API integration with Zapier MCP, parameter validation (path, query, body), authentication middleware, health check endpoint, enhanced error handling with web search for solutions, logging integration, and environment variable configuration.

### `generator/monitoring/` - Monitoring & Observability

**`logger.py`** - Request/response logging system. Should implement: structured logging for all agent activity, request/response tracking, Claude API call logging, error logging with context, and log rotation/storage.

**`metrics.py`** - Performance tracking. Should implement: request counting, success/failure rates, response time tracking, token usage monitoring, cost estimation, and metrics aggregation.

**`alerting.py`** - Error notifications. Should implement: critical error detection, alert dispatching (email/Slack/Discord), alert throttling, incident tracking, and resolution monitoring.

### `generator/runtime/` - Runtime Environment

**`deployed_agents/`** - Directory for running agent instances. Each deployed agent gets its own subdirectory with main.py, config.json, requirements.txt, and logs. Should implement: agent process management, lifecycle control (start/stop/restart), health checks, and resource monitoring.

### `generator/ui/` - User Interface

**`agent_dashboard.py`** - Web dashboard for monitoring deployed agents. Should implement: agent listing with status, metrics visualization, log viewing, error tracking, agent controls (restart/delete), and real-time updates.

**`testing_playground.py`** - Interactive API testing interface. Should implement: endpoint documentation, sample request generation, curl command generation, interactive request builder, response visualization, and request history.

## Key Features

- **Natural Language Input**: Describe workflows in plain English
- **Automatic API Design**: Generates appropriate REST endpoints (GET/POST/PUT/DELETE/PATCH) based on task
- **Zapier MCP Integration**: Single integration point for 8,000+ apps and 30,000+ actions
- **Template-Based Generation**: Reliable code generation using single flexible FastAPI template
- **Enhanced Error Handling**: Uses web search to find solutions to errors
- **Monitoring Dashboard**: Track performance, logs, and errors
- **Testing Playground**: Test generated APIs interactively
- **Simple Architecture**: All agents are on-demand API calls with flexible REST endpoints

## Implementation Phases

### Phase 1: Core Pipeline (MVP) ⚙️
- User input validation and prompt analysis
- Service and parameter extraction
- API design with appropriate HTTP methods and endpoints
- Code generation from single template using Claude
- Basic deployment functionality

### Phase 2: Essential Features 🔧
- Monitoring and logging system
- Enhanced error handling with web search
- Configuration management
- API key generation and authentication

### Phase 3: User Interface 🎨
- Agent monitoring dashboard
- Interactive testing playground
- API documentation generation

### Phase 4: Nice-to-Have 🚀
- Version control for agents
- Agent composition (chaining multiple agents)
- Cost tracking and optimization
- Batch operations support

## Getting Started

### Prerequisites
- Python 3.9+
- Anthropic API key (for Claude)
- Zapier MCP configured
- FastAPI and dependencies

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fuseai.git
cd fuseai

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Usage

**Backend API (create/list/deploy agents):**

```bash
# From project root
python -m api.server
# Or: uvicorn api.server:app --host 0.0.0.0 --port 8000
# API: http://localhost:8000  (CORS allowed for http://localhost:5173)
```

**Frontend (React/Vite):**

```bash
cd frontend
npm install
npm run dev
# UI: http://localhost:5173
# Set VITE_API_URL=http://localhost:8000/api (default) so the UI talks to the backend.
```

**Full flow:** Start the backend (port 8000), then the frontend (port 5173). Create an agent from the UI (prompt → create & deploy). The backend runs the design agent, generates code, saves to `runtime/agents_registry.json` and `runtime/deployed_agents/<id>/`, and starts the agent server on a free port (8001, 8002, …). Open an agent’s detail page to see custom endpoints and use “Try It Out” to run the agent via the backend proxy.

### Testing the planner (LangSmith)

To run the planner and inspect traces in **LangSmith**:

1. Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY`, and `LANGCHAIN_TRACING_V2=true`.
2. `pip install -r requirements.txt`
3. Run the planner (e.g. `python -c "from core.planner import run_planner; run_planner('...')"`).
4. Open [smith.langchain.com](https://smith.langchain.com) to view traces (nodes, LLM calls, state).

See **[docs/TESTING.md](docs/TESTING.md)** for full setup.

## Example Use Cases

- "Get all Trello cards assigned to a person and send summary to Slack" → `POST /summarize-cards`
- "Fetch GitHub issues from a repository and create Asana tasks" → `POST /sync-issues`
- "Get contact details from Salesforce by email" → `GET /contacts/{email}`
- "Update Jira ticket status" → `PUT /tickets/{ticket_id}`
- "Delete old Trello cards from a board" → `DELETE /cards/cleanup`

## How It Works

### User Input
```
"Get all Trello cards for a person and send them a summarization in Slack"
```

### Generated Agent
FuseAI creates a FastAPI agent with:
- **Endpoint**: Appropriate HTTP method and path (e.g., `POST /summarize`, `GET /contacts/{id}`, `PUT /update`)
- **Parameters**: Inferred from task (path params, query params, or request body)
- **Logic**: Calls Claude with Zapier MCP to execute the task
- **Result**: Returns structured response

### Agent Structure
Every generated agent:
1. Exposes RESTful endpoint(s) with appropriate HTTP methods
2. Validates API key authentication
3. Handles path parameters, query parameters, or request body as needed
4. Calls Claude with Zapier MCP
5. Zapier MCP handles all service integrations (Trello, Slack, etc.)
6. Returns structured result
7. Logs all activity for monitoring

## Architecture Decisions

- **Single template approach**: One flexible FastAPI template for all agents with dynamic endpoint generation
- **Zapier MCP only**: Single integration point provides access to 8,000+ apps without individual MCP configuration
- **Flexible REST design**: Supports GET/POST/PUT/DELETE/PATCH based on task semantics
- **API-only agents**: All agents are on-demand API calls (no webhooks or scheduled tasks for MVP)
- **Web search for errors**: High-value use case for intelligent error resolution
- **API-key authentication**: Simple and secure for MVP
- **File-based deployment**: Easy to manage, restart, and version agents
- **Confirmation before deploy**: User reviews plan before agent creation
- **Claude generates prompts**: Uses Claude to create optimal prompts for the agent's Claude API calls

## Technical Stack

- **FastAPI**: For generated agent APIs
- **Anthropic Claude**: Main AI orchestration with Zapier MCP
- **Zapier MCP**: Single integration point for all external services
- **Python 3.9+**: Core language
- **Uvicorn**: ASGI server for agents
- **Logging**: Built-in Python logging
- **File-based storage**: Simple deployment and management

## Agent Lifecycle

```
User Prompt
    ↓
Planner (extract services & parameters)
    ↓
API Designer (design appropriate endpoint: GET/POST/PUT/DELETE/PATCH)
    ↓
Code Generator (fill template with Claude-generated prompt)
    ↓
Deployer (create directory, install deps, start server)
    ↓
Running Agent (exposes API, handles requests via Claude + Zapier MCP)
```

---

## Quick Start Prompt for Collaborators

**Paste this to Claude when starting work:**

```
I'm working on FuseAI, an AI-powered agent generator that creates custom API agents from natural language descriptions.

PROJECT OVERVIEW:
- Users describe workflows in plain English (e.g., "Get Trello cards for a person and send summary to Slack")
- System analyzes prompt, extracts services/parameters, designs appropriate REST endpoint (GET/POST/PUT/DELETE/PATCH), generates FastAPI code from one template
- All agents use Claude with Zapier MCP (single integration for 8,000+ apps)
- Deploys agents with monitoring, error handling (using web search), and testing playground

ARCHITECTURE:
- generator/core/: planner.py (service & parameter extraction), api_designer.py (REST endpoint design with appropriate HTTP methods), code_generator.py (template filling), deployer.py (runtime deployment)
- generator/templates/: agent_template.py (single flexible FastAPI template for all agents)
- generator/monitoring/: logger.py (request/response logs), metrics.py (performance), alerting.py (notifications)
- generator/ui/: agent_dashboard.py (monitoring UI), testing_playground.py (interactive testing)

KEY FEATURES:
- Single template approach: one agent_template.py for all agents with flexible endpoint generation
- Zapier MCP: single integration point for all 8,000+ services
- REST-compliant agents: supports GET/POST/PUT/DELETE/PATCH based on task semantics
- API-only agents: all agents expose RESTful endpoints (no webhooks/scheduling)
- Web search for error solutions (main use of search)
- Claude generates Claude prompts: uses Claude to create optimal prompts for agent's task execution

SIMPLIFIED FLOW:
1. User describes task in plain English
2. Planner extracts services (Trello, Slack) and parameters (person_name, slack_user_id)
3. API Designer determines appropriate HTTP method and endpoint path (GET /contacts/{id}, POST /summarize, etc.)
4. Code Generator uses Claude to generate task prompt, fills template with endpoint configuration
5. Deployer creates agent directory, starts FastAPI server
6. Agent receives requests, calls Claude with Zapier MCP, returns results

TECH STACK:
- FastAPI for generated agents
- Anthropic Claude API with Zapier MCP
- Web search tool for error handling
- File-based deployment (runtime/deployed_agents/)
- Single Zapier MCP URL: https://mcp.zapier.com

CURRENT PHASE: [Specify which phase/feature you're working on]

Please help me implement [specific task] based on the architecture above.
```