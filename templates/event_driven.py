"""
Event-Driven Template for Forge Agents
Supports: scheduled, webhook, and on-demand triggers
"""

SCHEDULED_TEMPLATE = '''
from fastapi import FastAPI, HTTPException, Header
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from anthropic import Anthropic
from typing import Optional
import os
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="{agent_name}", description="{agent_description}")
scheduler = AsyncIOScheduler()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Error handling imports
{error_handler_import}

# Configuration
{config_variables}

# MCP Servers
MCP_SERVERS = {mcp_servers}

async def scheduled_task():
    """
    {task_description}
    Runs on schedule: {schedule_description}
    """
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            mcp_servers=MCP_SERVERS,
            messages=[{{
                "role": "user",
                "content": """{task_prompt}"""
            }}]
        )
        
        result = {{"content": [block.text for block in response.content if hasattr(block, "text")]}}
        logger_instance.log_success("scheduled_task", result)
        return result
        
    except Exception as e:
        solutions = await search_error_solutions(e)
        logger_instance.log_error("scheduled_task", e, {{"solutions": solutions}})
        raise

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(scheduled_task, "cron", {cron_kwargs})
    scheduler.start()
    logging.info("Scheduler started: {schedule_description}")

@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler.shutdown()

@app.get("/health")
async def health():
    jobs = scheduler.get_jobs()
    next_run = jobs[0].next_run_time.isoformat() if jobs else None
    return {{"status": "running", "next_run": next_run, "agent_id": "{agent_id}"}}

@app.post("/trigger-now")
async def trigger_now(x_api_key: str = Header(...)):
    """Manual trigger for testing"""
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    result = await scheduled_task()
    return {{"status": "triggered", "result": result}}

@app.get("/logs")
async def get_logs(limit: int = 50, x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {{"logs": logger_instance.get_recent_logs(limit)}}
'''

WEBHOOK_TEMPLATE = '''
from fastapi import FastAPI, HTTPException, Header, Request
from anthropic import Anthropic
from typing import Optional
import os
import logging
import hmac
import hashlib

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="{agent_name}", description="{agent_description}")
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Error handling imports
{error_handler_import}

# Configuration
{config_variables}

# MCP Servers
MCP_SERVERS = {mcp_servers}

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature if secret is configured"""
    if not secret:
        return True
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={{expected}}", signature)

async def process_webhook(payload: dict) -> dict:
    """
    {task_description}
    Triggered by: {trigger_description}
    """
    try:
        # Build dynamic prompt with webhook data
        prompt = f"""{task_prompt}

Webhook payload received:
{{payload}}
"""
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            mcp_servers=MCP_SERVERS,
            messages=[{{"role": "user", "content": prompt}}]
        )
        
        result = {{"content": [block.text for block in response.content if hasattr(block, "text")]}}
        logger_instance.log_success("webhook_process", result)
        return result
        
    except Exception as e:
        solutions = await search_error_solutions(e)
        logger_instance.log_error("webhook_process", e, {{"payload": str(payload)[:500], "solutions": solutions}})
        raise

@app.post("/webhook")
async def handle_webhook(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Webhook endpoint for external triggers
    Supports API key auth or webhook signature verification
    """
    # Auth check
    api_key = os.getenv("API_KEY")
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    
    if api_key and x_api_key != api_key:
        if webhook_secret:
            body = await request.body()
            if not verify_webhook_signature(body, x_webhook_signature or "", webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid authentication")
        else:
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    payload = await request.json()
    logger_instance.log_request("/webhook", payload)
    
    try:
        result = await process_webhook(payload)
        return {{"success": True, "result": result}}
    except Exception as e:
        if isinstance(e, EnhancedError):
            return {{"success": False, "error": e.to_dict()}}
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {{"status": "running", "agent_id": "{agent_id}", "type": "webhook"}}

@app.get("/logs")
async def get_logs(limit: int = 50, x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {{"logs": logger_instance.get_recent_logs(limit)}}
'''

ONDEMAND_TEMPLATE = '''
from fastapi import FastAPI, HTTPException, Header
from anthropic import Anthropic
from pydantic import BaseModel
from typing import Optional, Any
import os
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="{agent_name}", description="{agent_description}")
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Error handling imports
{error_handler_import}

# Configuration
{config_variables}

# MCP Servers
MCP_SERVERS = {mcp_servers}

class TaskRequest(BaseModel):
    {request_model_fields}

class TaskResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[dict] = None

async def execute_task(params: dict) -> dict:
    """
    {task_description}
    """
    try:
        prompt = f"""{task_prompt}

Parameters:
{{params}}
"""
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            mcp_servers=MCP_SERVERS,
            messages=[{{"role": "user", "content": prompt}}]
        )
        
        result = {{"content": [block.text for block in response.content if hasattr(block, "text")]}}
        logger_instance.log_success("execute_task", result)
        return result
        
    except Exception as e:
        solutions = await search_error_solutions(e)
        logger_instance.log_error("execute_task", e, {{"params": params, "solutions": solutions}})
        raise

@app.post("/{endpoint_path}", response_model=TaskResponse)
async def run_task(request: TaskRequest, x_api_key: str = Header(...)):
    """
    {endpoint_description}
    """
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    params = request.model_dump()
    logger_instance.log_request("/{endpoint_path}", params)
    
    try:
        result = await execute_task(params)
        return TaskResponse(success=True, result=result)
    except EnhancedError as e:
        return TaskResponse(success=False, error=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {{"status": "running", "agent_id": "{agent_id}", "type": "on_demand"}}

@app.get("/logs")
async def get_logs(limit: int = 50, x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {{"logs": logger_instance.get_recent_logs(limit)}}
'''

# Template selector
TEMPLATES = {
    "scheduled": SCHEDULED_TEMPLATE,
    "webhook": WEBHOOK_TEMPLATE,
    "on_demand": ONDEMAND_TEMPLATE
}

def get_template(trigger_type: str) -> str:
    """Get the appropriate template for the trigger type"""
    if trigger_type not in TEMPLATES:
        raise ValueError(f"Unknown trigger type: {trigger_type}. Must be one of: {list(TEMPLATES.keys())}")
    return TEMPLATES[trigger_type]

def parse_cron_to_kwargs(cron_expr: str) -> str:
    """Convert cron expression to APScheduler kwargs string"""
    parts = cron_expr.split()
    if len(parts) != 5:
        return 'hour=9, minute=0'  # Default to 9am
    
    minute, hour, day, month, dow = parts
    
    kwargs = []
    if minute != '*':
        kwargs.append(f'minute={minute}')
    if hour != '*':
        kwargs.append(f'hour={hour}')
    if day != '*':
        kwargs.append(f'day={day}')
    if month != '*':
        kwargs.append(f'month={month}')
    if dow != '*':
        kwargs.append(f'day_of_week={dow}')
    
    return ', '.join(kwargs) if kwargs else 'hour=9, minute=0'

def generate_request_model_fields(params: dict) -> str:
    """Generate Pydantic model fields from params dict"""
    type_map = {"string": "str", "int": "int", "float": "float", "bool": "bool"}
    
    fields = []
    for name, ptype in params.items():
        py_type = type_map.get(ptype, "str")
        fields.append(f'{name}: {py_type}')
    
    return '\n    '.join(fields) if fields else 'pass'