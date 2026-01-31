# FuseAI

An AI-powered agent builder that lets users describe a workflow in plain English and automatically generates, deploys, and monitors custom API agents.

## Overview

FuseAI analyzes natural language requests, designs REST APIs, selects Zapier integrations, generates FastAPI code from templates, and deploys running agents with monitoring, error handling, and a testing playground.

## Project Structure

### `generator/core/` - Core Generation Pipeline

**`planner.py`** - Analyzes user prompts and creates execution plans. Should implement: prompt parsing, requirement extraction, trigger type detection (webhook/scheduled/on-demand), feasibility validation using web search, and template selection based on requirements.

**`api_designer.py`** - Designs REST API structure for generated agents. Should implement: endpoint generation based on trigger types, parameter extraction for different services, authentication setup, and API documentation generation.

**`zapier_mapper.py`** - Maps requirements to Zapier actions. Should implement: service-to-Zapier action mapping, web search for available Zapier triggers/actions, action inference from user requirements, and Zapier API integration.

**`code_generator.py`** - Generates FastAPI code using templates. Should implement: template loading and rendering, formatting pattern discovery via web search, code generation with error handling, configuration file creation, and requirements.txt generation.

**`deployer.py`** - Deploys agents to runtime environment. Should implement: agent directory creation, file writing (main.py, config.json), dependency installation, FastAPI server startup, port management, API key generation, and monitoring setup.

### `generator/templates/` - Code Templates

**`fastapi_base.py`** - Base FastAPI boilerplate template. Should include: basic FastAPI app structure, authentication middleware, health check endpoints, CORS configuration, and environment variable loading.

**`zapier_integration.py`** - Zapier API client patterns. Should include: Zapier API authentication, action execution wrapper, retry logic, response parsing, and error handling patterns.

**`webhook_handler.py`** - Webhook trigger patterns. Should include: webhook endpoint template, payload validation, event extraction logic, signature verification, and async processing patterns.

**`scheduled_task.py`** - Cron/scheduled execution template. Should include: APScheduler integration, cron expression parsing, background task execution, schedule update endpoints, and status monitoring.

**`event_driven.py`** - Event-based triggers template. Should include: event listener setup, event queue management, event filtering logic, and event-to-action mapping.

**`error_handler.py`** - Enhanced error handling with web search. Should include: exception catching patterns, web search for solutions, error logging with context, user-friendly error responses, and retry strategies.

### `generator/monitoring/` - Monitoring & Observability

**`logger.py`** - Request/response logging system. Should implement: structured logging for all agent activity, request/response tracking, Zapier action logging, error logging with context, and log rotation/storage.

**`metrics.py`** - Performance tracking. Should implement: request counting, success/failure rates, response time tracking, token usage monitoring, cost estimation, and metrics aggregation.

**`alerting.py`** - Error notifications. Should implement: critical error detection, alert dispatching (email/Slack/Discord), alert throttling, incident tracking, and resolution monitoring.

### `generator/runtime/` - Runtime Environment

**`deployed_agents/`** - Directory for running agent instances. Each deployed agent gets its own subdirectory with main.py, config.json, requirements.txt, and logs. Should implement: agent process management, lifecycle control (start/stop/restart), health checks, and resource monitoring.

### `generator/ui/` - User Interface

**`agent_dashboard.py`** - Web dashboard for monitoring deployed agents. Should implement: agent listing with status, metrics visualization, log viewing, error tracking, agent controls (restart/delete), and real-time updates.

**`testing_playground.py`** - Interactive API testing interface. Should implement: endpoint documentation, sample request generation, curl command generation, interactive request builder, response visualization, and request history.

## Key Features

- **Natural Language Input**: Describe workflows in plain English
- **Automatic API Design**: Generates REST endpoints based on requirements
- **Zapier Integration**: Leverages 5000+ Zapier integrations
- **Template-Based Generation**: Reliable code generation using FastAPI templates
- **Enhanced Error Handling**: Uses web search to find solutions to errors
- **Monitoring Dashboard**: Track performance, logs, and errors
- **Testing Playground**: Test generated APIs interactively
- **Multiple Trigger Types**: Webhooks, scheduled tasks, and on-demand APIs

## Implementation Phases

### Phase 1: Core Pipeline (MVP) ⚙️
- User input validation and prompt analysis
- API design based on requirements
- Zapier action mapping
- Code generation from templates
- Basic deployment functionality

### Phase 2: Essential Features 🔧
- Monitoring and logging system
- Event triggers (webhooks + scheduled tasks)
- Enhanced error handling with web search
- Configuration management

### Phase 3: User Interface 🎨
- Agent monitoring dashboard
- Interactive testing playground
- API documentation generation

### Phase 4: Nice-to-Have 🚀
- Version control for agents
- Agent composition (chaining multiple agents)
- Cost tracking and optimization
- Advanced workflow patterns

## Getting Started

### Prerequisites
- Python 3.9+
- Anthropic API key (for Claude)
- Zapier API key
- FastAPI and dependencies

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/FuseAI.git
cd FuseAI

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Usage

```bash
# Start the generator
python main.py

# Access the dashboard
open http://localhost:8000
```

## Example Use Cases

- "When a card is added to Trello board, summarize it and send to Slack"
- "Every morning at 9am, fetch Asana tasks and send summary to Discord"
- "Create an API that takes GitHub issues and creates Jira tickets"
- "Monitor website uptime and alert me on Telegram if it's down"

## Architecture Decisions

- **Templates over generation**: Uses FastAPI templates for reliability and consistency
- **Zapier-only integrations**: Simplifies MCP configuration and provides 5000+ integrations
- **Web search for errors**: High-value use case for intelligent error resolution
- **API-key authentication**: Simple and secure for MVP
- **File-based deployment**: Easy to manage, restart, and version agents
- **Confirmation before deploy**: User reviews plan before agent creation

---

## Quick Start Prompt for Collaborators

**Paste this to Claude when starting work:**

```
I'm working on FuseAI, an AI-powered agent generator that creates custom API agents from natural language descriptions.

PROJECT OVERVIEW:
- Users describe workflows in plain English (e.g., "When Trello card added, summarize and send to Slack")
- System analyzes prompt, designs REST API, maps to Zapier actions, generates FastAPI code from templates
- Deploys agents with monitoring, error handling (using web search), and testing playground

ARCHITECTURE:
- generator/core/: planner.py (prompt analysis), api_designer.py (endpoint design), zapier_mapper.py (service mapping), code_generator.py (template rendering), deployer.py (runtime deployment)
- generator/templates/: FastAPI templates for webhooks, scheduled tasks, Zapier integration, error handling
- generator/monitoring/: logger.py (request/response logs), metrics.py (performance), alerting.py (notifications)
- generator/ui/: agent_dashboard.py (monitoring UI), testing_playground.py (interactive testing)

KEY FEATURES:
- Template-based FastAPI code generation (not full LLM generation)
- Zapier for all integrations (5000+ services)
- Web search for error solutions (main use of search)
- Three trigger types: webhooks, scheduled (cron), on-demand APIs
- Monitoring dashboard shows metrics, logs, errors for all deployed agents

TECH STACK:
- FastAPI for generated agents
- Anthropic Claude API with web search tool
- Zapier API for integrations
- APScheduler for scheduled tasks
- File-based deployment (runtime/deployed_agents/)

CURRENT PHASE: [Specify which phase/feature you're working on]

Please help me implement [specific task] based on the architecture above.
```
