# Testing the planner with LangSmith

This guide covers how to run the planner locally and use **LangSmith** for tracing and debugging. Traces show each node (validate_task → extract_services → extract_parameters → suggest_endpoint → format_task_description), inputs/outputs, and LLM calls.

Works with **any supported Python** (3.9+); no LangGraph Studio CLI required.

## Prerequisites

- **Python 3.9+**
- **Anthropic API key** (for the planner’s LLM)
- **LangSmith account** (free at [smith.langchain.com](https://smith.langchain.com))

## 1. Environment

From the project root:

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
# Required for the planner LLM
ANTHROPIC_API_KEY=your-anthropic-api-key

# Required for LangSmith tracing (get key at https://smith.langchain.com)
LANGSMITH_API_KEY=your-langsmith-api-key
LANGCHAIN_TRACING_V2=true
```

Optional: set a project name so traces go to a dedicated project:

```bash
LANGCHAIN_PROJECT=FuseAI-planner
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` includes `langsmith`, which LangGraph/LangChain use for tracing when `LANGCHAIN_TRACING_V2=true`.

## 3. Run the planner

From the project root:

```bash
python -c "
from core.planner import run_planner

result = run_planner('Get all Trello cards for a person and send them a summarization in Slack')
print('task_description:', result.get('task_description', '')[:500])
print('services:', result.get('services'))
print('parameters:', result.get('parameters'))
"
```

Or from your own script:

```python
from core.planner import run_planner

result = run_planner("Your workflow description here")
```

## 4. View traces in LangSmith

1. Go to [smith.langchain.com](https://smith.langchain.com) and sign in.
2. Open **Projects** (or **Traces**). Your run will appear under the default project or `FuseAI-planner` if you set `LANGCHAIN_PROJECT`.
3. Click a trace to see:
   - The full graph run (each node as a step)
   - Inputs and outputs per node
   - LLM requests and responses (prompts, structured output)
   - Latency and token usage

You can filter by project, time range, and tags to debug failures or compare runs.

## 5. Optional: run name and metadata

To tag runs for easier filtering:

```python
from core.planner import create_planner

planner = create_planner()
result = planner.invoke(
    {"user_prompt": "Get Trello cards and send to Slack"},
    config={"run_name": "test-summarize", "tags": ["planner", "test"]},
)
```

Then in LangSmith you can filter by `run_name` or `tags`.

## Summary

| Step | Action |
|------|--------|
| 1 | Copy `.env.example` → `.env`, set `ANTHROPIC_API_KEY`, `LANGSMITH_API_KEY`, `LANGCHAIN_TRACING_V2=true` |
| 2 | `pip install -r requirements.txt` |
| 3 | Run the planner (`run_planner(...)` or the one-liner above) |
| 4 | Open [smith.langchain.com](https://smith.langchain.com) and inspect traces |

No extra CLI or Python version constraints; LangSmith works with your current environment.
