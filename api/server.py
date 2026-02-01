"""
Backend API for FuseAI: create/list/get agents, deploy, and proxy run.
Integrates core (design agent → code generator → deployer) with the frontend.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

# Project root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.registry import (
    add_agent,
    get_agent as get_agent_from_registry,
    list_agents,
    reserve_port,
    update_agent,
)
from monitoring.logger import delete_agent_logs, log_error, log_info, get_logs as get_agent_logs
from monitoring.metrics import delete_agent_metrics, get_metrics as get_agent_metrics, record_call

# In-memory process registry: agent_id -> {"process": Popen, "port": int}
_agent_processes: dict[str, dict[str, Any]] = {}
# Agents that have passed port check (actually listening)
_agent_ready: set[str] = set()
_port_check_stop = threading.Event()


def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except (OSError, socket.error):
        return False


def _port_check_loop() -> None:
    while not _port_check_stop.is_set():
        for agent_id, info in list(_agent_processes.items()):
            if agent_id in _agent_ready:
                continue
            proc = info.get("process")
            port = info.get("port")
            if proc is None or port is None or proc.poll() is not None:
                continue
            if _is_port_open("127.0.0.1", port):
                _agent_ready.add(agent_id)
                update_agent(agent_id, {"status": "running"})
        _port_check_stop.wait(timeout=2.0)


def _start_all_agents() -> None:
    """On server startup: deploy every agent in the registry that has code on disk."""
    from core.deployer import get_agent_dir

    for agent in list_agents():
        agent_id = agent.get("id")
        if not agent_id:
            continue
        agent_dir = get_agent_dir(agent_id, project_root=_ROOT)
        if not (agent_dir / "main.py").exists():
            continue
        port = agent.get("port") or reserve_port()
        if agent.get("port") is None:
            update_agent(agent_id, {"port": port})
        env = os.environ.copy()
        env["FUSEAI_AGENT_ID"] = agent_id
        env["FUSEAI_PORT"] = str(port)
        env["FUSEAI_ROOT"] = str(_ROOT)
        cmd = [
            sys.executable,
            "-c",
            "import os, sys; "
            "sys.path.insert(0, os.environ['FUSEAI_ROOT']); "
            "from pathlib import Path; "
            "from core.deployer import deploy_agent; "
            "root = Path(os.environ['FUSEAI_ROOT']).resolve(); "
            "deploy_agent(agent_id=os.environ['FUSEAI_AGENT_ID'], port=int(os.environ['FUSEAI_PORT']), project_root=root)",
        ]
        proc = subprocess.Popen(
            cmd,
            cwd=str(_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        _agent_processes[agent_id] = {"process": proc, "port": port}
        update_agent(agent_id, {"status": "deploying"})


def _start_port_check_thread() -> None:
    t = threading.Thread(target=_port_check_loop, daemon=True)
    t.start()


app = FastAPI(title="FuseAI API", version="1.0.0")


@app.on_event("startup")
def on_startup() -> None:
    _start_all_agents()
    _start_port_check_thread()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/response models ---
class CreateAgentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Workflow task description")
    name: str | None = Field(None, description="Optional display name (default from plan)")


class AnalyzeAgentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Workflow task description")


class DeployAgentRequest(BaseModel):
    port: int | None = Field(None, description="Port (default: next available)")


class RunAgentRequest(BaseModel):
    method: str = Field("POST", description="HTTP method")
    path: str = Field(..., description="Path (e.g. /execute)")
    query: dict[str, str] | None = Field(None, description="Query params")
    body: dict[str, Any] | None = Field(None, description="JSON body for POST/PUT")


# --- Helpers ---
def _run_design_and_generate(prompt: str) -> tuple[dict[str, Any], Path]:
    from core.agent import run_design_agent
    from core.code_generator import generate_agent

    state = run_design_agent(prompt)
    context = state.get("context_for_coding_agent")
    if not context:
        raise ValueError("Design agent did not produce context_for_coding_agent")

    agent_id = f"agent_{int(time.time())}"
    main_py = generate_agent(
        context_for_coding_agent=context,
        agent_id=agent_id,
    )
    return context, main_py.parent


def _agent_payload(agent: dict[str, Any]) -> dict[str, Any]:
    """Shape agent for frontend: id, name, description, status, services, endpoints, port, baseUrl."""
    port = agent.get("port")
    base_url = f"http://localhost:{port}" if port else None
    return {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "description": agent.get("description"),
        "prompt": agent.get("prompt"),
        "status": agent.get("status", "created"),
        "triggerType": "on_demand",
        "services": agent.get("services", []),
        "endpoints": agent.get("endpoints", []),
        "task_description": agent.get("task_description"),
        "port": port,
        "baseUrl": base_url,
        "apiUrl": base_url,
        "created_at": agent.get("created_at"),
    }


def _ensure_process_status() -> None:
    """Update registry status from running processes."""
    for agent_id, info in list(_agent_processes.items()):
        proc = info.get("process")
        if proc is None or proc.poll() is not None:
            update_agent(agent_id, {"status": "stopped"})
            _agent_processes.pop(agent_id, None)
            _agent_ready.discard(agent_id)


def _suggest_name_from_task(task_description: str) -> str:
    """Derive a short display name from task description first line."""
    if not task_description or not task_description.strip():
        return "Generated Agent"
    first = task_description.strip().split("\n")[0].strip()
    if first.lower().startswith("task:"):
        first = first[5:].strip()
    return (first[:80] if first else "Generated Agent") or "Generated Agent"


# --- Routes ---
@app.post("/api/agents/analyze")
def api_analyze_agent(body: AnalyzeAgentRequest) -> dict[str, Any]:
    """Analyze prompt only (planner + API designer). Returns LLM-suggested name, services, endpoints. No code gen or deploy."""
    try:
        from core.zapier_mapper import get_planner_context
        ctx = get_planner_context(body.prompt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    api_design = ctx.get("api_design") or {}
    task_description = (ctx.get("task_description") or "").strip()
    suggested_name = (ctx.get("suggested_agent_name") or "").strip() or _suggest_name_from_task(task_description)
    return {
        "suggestedName": suggested_name,
        "services": list(ctx.get("services") or []),
        "endpoints": list(api_design.get("endpoints") or []),
        "task_description": task_description,
    }


@app.get("/api/env-schema")
def api_env_schema() -> list[dict[str, str]]:
    """Return env variable names and descriptions for the Settings UI (no values)."""
    return [
        {"name": "ANTHROPIC_API_KEY", "description": "Required for planner and code generator. Get from console.anthropic.com."},
        {"name": "ZAPIER_MCP_SERVER_URL", "description": "Zapier MCP server URL. Get from mcp.zapier.com."},
        {"name": "ZAPIER_MCP_SECRET", "description": "Zapier MCP secret. Get from mcp.zapier.com."},
        {"name": "LANGSMITH_API_KEY", "description": "Optional. For LangSmith tracing."},
        {"name": "LANGCHAIN_TRACING_V2", "description": "Optional. Set to true to enable tracing."},
        {"name": "LANGCHAIN_PROJECT", "description": "Optional. LangSmith project name."},
    ]


@app.get("/api/agents")
def api_list_agents() -> list[dict[str, Any]]:
    _ensure_process_status()
    agents = list_agents()
    # Sync status: running only when port is ready, else deploying
    for a in agents:
        aid = a.get("id")
        if aid in _agent_processes:
            a["port"] = _agent_processes[aid].get("port")
            a["baseUrl"] = f"http://localhost:{_agent_processes[aid].get('port')}"
            a["apiUrl"] = a["baseUrl"]
            a["status"] = "running" if aid in _agent_ready else "deploying"
        else:
            # Keep registry status (stopped, created, etc.)
            pass
    return [_agent_payload(a) for a in agents]


@app.get("/api/agents/{agent_id}")
def api_get_agent(agent_id: str) -> dict[str, Any]:
    _ensure_process_status()
    agent = get_agent_from_registry(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent_id in _agent_processes:
        agent["port"] = _agent_processes[agent_id].get("port")
        agent["baseUrl"] = f"http://localhost:{_agent_processes[agent_id].get('port')}"
        agent["apiUrl"] = agent["baseUrl"]
        agent["status"] = "running" if agent_id in _agent_ready else "deploying"
    return _agent_payload(agent)


@app.post("/api/agents")
def api_create_agent(body: CreateAgentRequest) -> dict[str, Any]:
    """Create agent: design → generate → save to registry → deploy in background."""
    try:
        context, agent_dir = _run_design_and_generate(body.prompt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    agent_id = agent_dir.name
    api_design = context.get("api_design") or {}
    endpoints = api_design.get("endpoints") or []
    services = list(context.get("services") or [])
    task_description = (context.get("task_description") or "").strip()

    # Name: user-provided, or LLM-suggested from planner context, or fallback from task
    name = (body.name or "").strip()
    if not name:
        name = (context.get("suggested_agent_name") or "").strip()
    if not name and task_description:
        name = task_description.split("\n")[0].strip()
        if name.lower().startswith("task:"):
            name = name[5:].strip()
        name = (name or "Generated Agent")[:80]
    if not name:
        name = "Generated Agent"

    port = reserve_port()
    agent_record = {
        "id": agent_id,
        "name": name,
        "description": task_description[:200] if task_description else "",
        "prompt": body.prompt,
        "status": "created",
        "triggerType": "on_demand",
        "services": services,
        "endpoints": endpoints,
        "task_description": task_description,
        "port": port,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    add_agent(agent_record)

    # Deploy in background (subprocess)
    env = os.environ.copy()
    env["FUSEAI_AGENT_ID"] = agent_id
    env["FUSEAI_PORT"] = str(port)
    env["FUSEAI_ROOT"] = str(_ROOT)
    cmd = [
        sys.executable,
        "-c",
        "import os, sys; "
        "sys.path.insert(0, os.environ['FUSEAI_ROOT']); "
        "from pathlib import Path; "
        "from core.deployer import deploy_agent; "
        "root = Path(os.environ['FUSEAI_ROOT']).resolve(); "
        "deploy_agent(agent_id=os.environ['FUSEAI_AGENT_ID'], port=int(os.environ['FUSEAI_PORT']), project_root=root)",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _agent_processes[agent_id] = {"process": proc, "port": port}
    update_agent(agent_id, {"status": "deploying"})

    agent_record["status"] = "deploying"
    return _agent_payload(agent_record)


@app.post("/api/agents/{agent_id}/deploy")
def api_deploy_agent(agent_id: str, body: DeployAgentRequest | None = None) -> dict[str, Any]:
    """Start (or restart) the agent server."""
    agent = get_agent_from_registry(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Stop existing if any
    if agent_id in _agent_processes:
        p = _agent_processes[agent_id].get("process")
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        _agent_processes.pop(agent_id, None)
        _agent_ready.discard(agent_id)

    port = (body and body.port) or agent.get("port") or reserve_port()
    env = os.environ.copy()
    env["FUSEAI_AGENT_ID"] = agent_id
    env["FUSEAI_PORT"] = str(port)
    env["FUSEAI_ROOT"] = str(_ROOT)
    cmd = [
        sys.executable,
        "-c",
        "import os, sys; "
        "sys.path.insert(0, os.environ['FUSEAI_ROOT']); "
        "from pathlib import Path; "
        "from core.deployer import deploy_agent; "
        "root = Path(os.environ['FUSEAI_ROOT']).resolve(); "
        "deploy_agent(agent_id=os.environ['FUSEAI_AGENT_ID'], port=int(os.environ['FUSEAI_PORT']), project_root=root)",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _agent_processes[agent_id] = {"process": proc, "port": port}
    update_agent(agent_id, {"status": "deploying", "port": port})
    return _agent_payload({**agent, "status": "deploying", "port": port})


@app.post("/api/agents/{agent_id}/stop")
def api_stop_agent(agent_id: str) -> dict[str, Any]:
    if agent_id not in _agent_processes:
        agent = get_agent_from_registry(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        update_agent(agent_id, {"status": "stopped"})
        return _agent_payload({**agent, "status": "stopped"})

    p = _agent_processes[agent_id].get("process")
    if p and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    _agent_processes.pop(agent_id, None)
    _agent_ready.discard(agent_id)
    update_agent(agent_id, {"status": "stopped"})
    agent = get_agent_from_registry(agent_id) or {}
    return _agent_payload({**agent, "status": "stopped"})


def _agent_request_timeout() -> int:
    """Timeout in seconds for proxied agent requests (env FUSEAI_AGENT_REQUEST_TIMEOUT, default 300)."""
    try:
        return max(10, int(os.environ.get("FUSEAI_AGENT_REQUEST_TIMEOUT", "300")))
    except (ValueError, TypeError):
        return 300


@app.post("/api/agents/{agent_id}/test")
def api_test_agent(agent_id: str, body: RunAgentRequest) -> dict[str, Any]:
    """Proxy a request to the deployed agent (for Try It Out in UI). Records metrics and logs failures."""
    if agent_id not in _agent_processes:
        raise HTTPException(status_code=400, detail="Agent is not running. Deploy it first.")
    port = _agent_processes[agent_id].get("port")
    if not port:
        raise HTTPException(status_code=400, detail="Agent port unknown")

    import urllib.request
    import urllib.error

    url = f"http://127.0.0.1:{port}{body.path}"
    if body.query:
        from urllib.parse import urlencode
        url += "?" + urlencode(body.query)

    req_data = None
    if body.body and body.method in ("POST", "PUT", "PATCH"):
        import json as _json
        req_data = _json.dumps(body.body).encode("utf-8")

    timeout_sec = _agent_request_timeout()
    start = time.perf_counter()
    elapsed_ms = 0
    status = 0
    out_body = {}
    try:
        req = urllib.request.Request(url, data=req_data, method=body.method)
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            status = resp.status
            resp_body = resp.read().decode("utf-8", errors="replace")
            try:
                out_body = __import__("json").loads(resp_body)
            except Exception:
                out_body = {"raw": resp_body}
            record_call(agent_id, status, elapsed_ms, body.path)
            log_info(agent_id, f"Request {body.method} {body.path} completed", {"status": status, "duration_ms": elapsed_ms})
            return {"status": status, "duration": elapsed_ms, "body": out_body}
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        status = e.code
        try:
            err_body = e.read().decode("utf-8", errors="replace")
            out_body = __import__("json").loads(err_body)
        except Exception:
            out_body = {"error": str(e)}
        record_call(agent_id, status, elapsed_ms, body.path)
        detail = out_body.get("detail", out_body.get("error", str(out_body)))
        if isinstance(detail, str):
            err_msg = f"Request failed: HTTP {e.code} — {detail}"
        else:
            err_msg = f"Request failed: HTTP {e.code} — {out_body.get('error', str(out_body))}"
        log_error(agent_id, err_msg, {"status": e.code, "path": body.path, "body": out_body})
        return {"status": e.code, "duration": elapsed_ms, "body": out_body}
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        record_call(agent_id, 0, elapsed_ms, body.path)
        err_msg = str(e)
        log_error(agent_id, f"Request failed: {err_msg}", {"path": body.path, "error": err_msg})
        return {"status": 0, "duration": elapsed_ms, "body": {"error": err_msg}}


@app.get("/api/agents/{agent_id}/code")
def api_get_agent_code(agent_id: str, file: str | None = None) -> dict[str, Any]:
    """Return generated code files for the agent. If file=main.py|config.json|README.md|requirements.txt return that only; else return { files: { main.py: ..., config.json: ..., ... } }."""
    from core.deployer import get_agent_dir

    agent_dir = get_agent_dir(agent_id, project_root=_ROOT)
    main_py = agent_dir / "main.py"
    if not main_py.exists():
        raise HTTPException(status_code=404, detail="Agent code not found")

    allowed = ("main.py", "config.json", "README.md", "requirements.txt")
    if file:
        if file not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid file. Allowed: {allowed}")
        path = agent_dir / file
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"File {file} not found")
        return {"file": file, "content": path.read_text(encoding="utf-8")}

    files = {}
    for name in allowed:
        p = agent_dir / name
        if p.exists():
            files[name] = p.read_text(encoding="utf-8")
    if "main.py" not in files:
        files["main.py"] = main_py.read_text(encoding="utf-8")
    return {"files": files, "code": files.get("main.py", "")}


@app.get("/api/agents/{agent_id}/metrics")
def api_get_agent_metrics(agent_id: str) -> dict[str, Any]:
    """Return per-agent metrics (API call counts, success rate, response times)."""
    if not get_agent_from_registry(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    return get_agent_metrics(agent_id)


@app.get("/api/agents/{agent_id}/logs")
def api_get_agent_logs(agent_id: str, level: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return per-agent log entries (errors and info from API calls)."""
    if not get_agent_from_registry(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    return get_agent_logs(agent_id, level=level, limit=limit)


@app.delete("/api/agents/{agent_id}")
def api_delete_agent(agent_id: str) -> dict[str, str]:
    """Stop if running, remove from registry, and completely delete the deployed agent (directory, metrics, logs)."""
    if agent_id in _agent_processes:
        p = _agent_processes[agent_id].get("process")
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        _agent_processes.pop(agent_id, None)
    from api.registry import remove_agent
    if not remove_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    # Delete deployed agent directory and all files inside
    from core.deployer import get_agent_dir
    import shutil
    agent_dir = get_agent_dir(agent_id, project_root=_ROOT)
    if agent_dir.exists():
        shutil.rmtree(agent_dir, ignore_errors=True)

    _agent_ready.discard(agent_id)
    # Delete per-agent metrics and logs
    delete_agent_metrics(agent_id)
    delete_agent_logs(agent_id)

    return {"message": "Agent removed"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
