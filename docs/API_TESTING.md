# Testing the Design API

How to run and test the unified design agent (planner → API designer → Zapier tool selection with LLM).

## Prerequisites

1. **Environment variables** (in `.env` in project root):
   - `ANTHROPIC_API_KEY` — required for planner and tool-selection LLM (get from [Anthropic](https://console.anthropic.com)).
   - `ZAPIER_MCP_SERVER_URL` and `ZAPIER_MCP_SECRET` — required for Zapier tools (get from [mcp.zapier.com](https://mcp.zapier.com): create an MCP server, add tools, then Connect → copy server URL and secret).
   - Optional: `LANGSMITH_API_KEY`, `LANGCHAIN_TRACING_V2=true` for traces (see [TESTING.md](TESTING.md)).

2. **Dependencies** (from project root):
   ```bash
   pip install -r requirements.txt
   ```

## 1. Start the API

From the project root:

```bash
uvicorn api.main:app --reload
```

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- OpenAPI docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 2. Quick health check

```bash
curl http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`

## 3. Test POST /design

Runs the unified design agent: planner → API designer → load Zapier tools → LLM selects tools → returns `context_for_coding_agent` (api_design + selected_zapier_tools) for the coding agent.

```bash
curl -X POST "http://127.0.0.1:8000/design" \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "Analyze cards in a Trello board and post a health report to Slack. User provides board_id."}'
```

Response: `{ "success": true, "context_for_coding_agent": { "api_design": {...}, "selected_zapier_tools": [...], "task_description": "...", "services": [...], "parameters": [...] }, "error": null }`.  
This can take 60–120 seconds (planner + api_designer + Zapier + LLM tool selection).

## 4. Run the test script

From project root (with the API already running in another terminal):

```bash
# Default prompt (Trello + Slack)
python scripts/test_agent_api.py

# Custom prompt
python scripts/test_agent_api.py --prompt "Reassign Trello cards and notify people on Slack. User provides board_id and slack_channel_id."

# Custom base URL
python scripts/test_agent_api.py --base-url http://localhost:8000
```

## 5. Testing a deployed agent (generated main.py)

After running the full workflow (`scripts/test_full_workflow.py`), the code generator writes an agent to `runtime/deployed_agents/<agent_id>/main.py`. To run and test that agent:

**From project root:**

```bash
# Run the agent (default port 8001 so it doesn't clash with the design API on 8000)
python scripts/run_deployed_agent.py <agent_id>

# Example
python scripts/run_deployed_agent.py agent_1769910594

# Custom port
python scripts/run_deployed_agent.py agent_1769910594 --port 8002
```

Then in another terminal (or browser):

```bash
# Health check
curl http://localhost:8001/health

# OpenAPI docs (paths depend on your api_design)
open http://localhost:8001/docs
```

Call the agent’s endpoints as defined in its API (e.g. `POST /analyze-cards-create-events/{board_id}`). The exact paths come from the design agent’s `api_design.endpoints`.

To list deployed agents: `ls runtime/deployed_agents/`

## Troubleshooting

- **"ZAPIER_MCP_SERVER_URL and ZAPIER_MCP_SECRET must be set"**  
  Add both to `.env` from your Zapier MCP server’s Connect / embed settings.

- **"No Zapier MCP tools available"**  
  In [mcp.zapier.com](https://mcp.zapier.com), add tools for the apps you need (e.g. Trello, Slack). The LLM will select from the full list.

- **Planner validation failed**  
  The task prompt didn’t pass the planner’s validation. Check `validation_reason` in the response or in `planner_context`.

- **Slow responses**  
  Planner + API designer + Zapier + LLM tool selection can take 60–120 seconds. Use `/health` for a fast check.
