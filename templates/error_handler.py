"""
Error Handler Template for Forge Agents
Provides enhanced error handling with web search for solutions
"""

ERROR_HANDLER_TEMPLATE = '''
import asyncio
import logging
from datetime import datetime
from typing import Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class EnhancedError(Exception):
    """Error with context and AI-powered solutions"""
    
    def __init__(self, original: Exception, context: dict = None, solutions: list = None):
        self.original = original
        self.context = context or {}
        self.solutions = solutions or []
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(str(original))
    
    def to_dict(self) -> dict:
        return {
            "error": str(self.original),
            "error_type": type(self.original).__name__,
            "timestamp": self.timestamp,
            "context": self.context,
            "solutions": self.solutions
        }

async def search_error_solutions(error: Exception, service: str = None) -> list:
    """
    Use web search to find solutions for errors
    
    Args:
        error: The exception that occurred
        service: Optional service name for context (e.g., "Trello", "Slack")
    
    Returns:
        List of possible solutions found via web search
    """
    error_type = type(error).__name__
    error_msg = str(error)[:200]
    
    query = f"{service + ' ' if service else ''}API error {error_type}: {error_msg} solution"
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{
                "role": "user",
                "content": f"""Find solutions for this error. Be concise and actionable.
                
Error Type: {error_type}
Error Message: {error_msg}
Service: {service or 'Unknown'}

Return 2-3 specific solutions."""
            }]
        )
        
        solutions = []
        for block in response.content:
            if block.type == "text" and block.text.strip():
                solutions.append(block.text.strip())
        
        return solutions[:3]
        
    except Exception as search_error:
        logger.warning(f"Error search failed: {search_error}")
        return [f"Could not fetch solutions: {str(search_error)}"]

async def execute_with_retry(
    func,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    service: str = None,
    context: dict = None
):
    """
    Execute a function with retry logic and enhanced error handling
    
    Args:
        func: Async function to execute
        max_retries: Maximum retry attempts
        backoff_base: Base for exponential backoff
        service: Service name for error context
        context: Additional context for logging
    
    Returns:
        Function result or raises EnhancedError
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return await func()
            
        except Exception as e:
            last_error = e
            
            if attempt < max_retries - 1:
                wait_time = backoff_base ** attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed: {e}")
    
    solutions = await search_error_solutions(last_error, service)
    
    raise EnhancedError(
        original=last_error,
        context={"service": service, "attempts": max_retries, **(context or {})},
        solutions=solutions
    )

class AgentLogger:
    """Logger for agent activity with structured output"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logs = []
    
    def _log(self, level: str, event: str, data: dict = None):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "level": level,
            "event": event,
            "data": data or {}
        }
        self.logs.append(entry)
        
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.agent_id}] {event}: {data}")
        
        return entry
    
    def log_request(self, endpoint: str, params: dict):
        return self._log("INFO", "request_received", {
            "endpoint": endpoint,
            "params": {k: "***" if "key" in k.lower() or "token" in k.lower() else v 
                      for k, v in params.items()}
        })
    
    def log_mcp_call(self, mcp_name: str, action: str, duration_ms: float = None):
        return self._log("INFO", "mcp_call", {
            "mcp": mcp_name,
            "action": action,
            "duration_ms": duration_ms
        })
    
    def log_success(self, task: str, result: dict = None):
        return self._log("INFO", "task_success", {
            "task": task,
            "result_preview": str(result)[:200] if result else None
        })
    
    def log_error(self, task: str, error: Exception, context: dict = None):
        if isinstance(error, EnhancedError):
            return self._log("ERROR", "task_failed", {
                "task": task,
                **error.to_dict(),
                **(context or {})
            })
        return self._log("ERROR", "task_failed", {
            "task": task,
            "error": str(error),
            "error_type": type(error).__name__,
            **(context or {})
        })
    
    def get_recent_logs(self, limit: int = 100) -> list:
        return self.logs[-limit:]
    
    def get_error_logs(self) -> list:
        return [log for log in self.logs if log["level"] == "ERROR"]
'''

# Helper to inject error handler into generated code
def inject_error_handler(agent_id: str) -> str:
    """Returns the error handler code with agent_id configured"""
    return ERROR_HANDLER_TEMPLATE + f"\n\nlogger_instance = AgentLogger('{agent_id}')\n"