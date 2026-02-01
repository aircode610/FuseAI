"""
Backend API for FuseAI: create/list/get agents, deploy, and proxy run.
Integrates core (design agent → code generator → deployer) with the frontend.
"""

from __future__ import annotations

import os
import subprocess
import sys
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

# In-memory process registry: agent_id -> {"process": Popen, "port": int}
_agent_processes: dict[str, dict[str, Any]] = {}

app = FastAPI(title="FuseAI API", version="1.0.0")

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
        "triggerType": agent.get("triggerType", "webhook"),
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


# --- Routes ---
@app.get("/api/agents")
def api_list_agents() -> list[dict[str, Any]]:
    _ensure_process_status()
    agents = list_agents()
    # Sync status from running processes
    for a in agents:
        aid = a.get("id")
        if aid in _agent_processes:
            a["status"] = "running"
            a["port"] = _agent_processes[aid].get("port")
            a["baseUrl"] = f"http://localhost:{_agent_processes[aid].get('port')}"
            a["apiUrl"] = a["baseUrl"]
    return [_agent_payload(a) for a in agents]


@app.get("/api/agents/{agent_id}")
def api_get_agent(agent_id: str) -> dict[str, Any]:
    _ensure_process_status()
    agent = get_agent_from_registry(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent_id in _agent_processes:
        agent["status"] = "running"
        agent["port"] = _agent_processes[agent_id].get("port")
        agent["baseUrl"] = f"http://localhost:{_agent_processes[agent_id].get('port')}"
        agent["apiUrl"] = agent["baseUrl"]
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

    # Name from first endpoint summary or task first line
    name = body.name
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
        "triggerType": "webhook",
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
    update_agent(agent_id, {"status": "stopped"})
    agent = get_agent_from_registry(agent_id) or {}
    return _agent_payload({**agent, "status": "stopped"})


@app.post("/api/agents/{agent_id}/test")
def api_test_agent(agent_id: str, body: RunAgentRequest) -> dict[str, Any]:
    """Proxy a request to the deployed agent (for Try It Out in UI)."""
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

    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, data=req_data, method=body.method)
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=60) as resp:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            resp_body = resp.read().decode("utf-8", errors="replace")
            try:
                data = __import__("json").loads(resp_body)
            except Exception:
                data = {"raw": resp_body}
            return {
                "status": resp.status,
                "duration": elapsed_ms,
                "body": data,
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        try:
            err_body = e.read().decode("utf-8", errors="replace")
            data = __import__("json").loads(err_body)
        except Exception:
            data = {"error": str(e)}
        return {"status": e.code, "duration": elapsed_ms, "body": data}
    except Exception as e:
        return {"status": 0, "duration": 0, "body": {"error": str(e)}}


@app.get("/api/agents/{agent_id}/code")
def api_get_agent_code(agent_id: str) -> dict[str, str]:
    """Return generated main.py content."""
    from core.deployer import get_agent_dir

    agent_dir = get_agent_dir(agent_id, project_root=_ROOT)
    main_py = agent_dir / "main.py"
    if not main_py.exists():
        raise HTTPException(status_code=404, detail="Agent code not found")
    return {"code": main_py.read_text(encoding="utf-8")}


@app.delete("/api/agents/{agent_id}")
def api_delete_agent(agent_id: str) -> dict[str, str]:
    """Stop if running and remove from registry (does not delete runtime files)."""
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
    return {"message": "Agent removed"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
