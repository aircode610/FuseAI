"""
FuseAI - Base FastAPI Template
This template provides the foundational structure for all generated agents.
"""

from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime
import uvicorn

# Configuration
API_KEY = os.getenv("AGENT_API_KEY", "default-key-change-me")
PORT = int(os.getenv("AGENT_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Logging setup
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="{{AGENT_NAME}}",
    description="{{AGENT_DESCRIPTION}}",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on deployment needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key authentication"""
    if api_key is None:
        logger.warning("Request made without API key")
        raise HTTPException(
            status_code=401,
            detail="Missing API Key. Include X-API-Key header."
        )
    if api_key != API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key

# Request/Response Models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    agent: str
    version: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Response: {response.status_code} | Duration: {duration:.3f}s"
        )
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Health check endpoint (public)
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint to verify agent is running.
    No authentication required.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        agent="{{AGENT_NAME}}",
        version="1.0.0"
    )

# Status endpoint (authenticated)
@app.get("/status", response_model=Dict[str, Any], tags=["System"])
async def get_status(api_key: str = Depends(verify_api_key)):
    """
    Get detailed agent status and configuration.
    Requires authentication.
    """
    return {
        "agent": "{{AGENT_NAME}}",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "configuration": {
            "port": PORT,
            "log_level": LOG_LEVEL,
            "endpoints": len(app.routes)
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )

# {{GENERATED_ENDPOINTS}}
# Agent-specific endpoints will be injected here during generation

if __name__ == "__main__":
    logger.info(f"Starting {{AGENT_NAME}} on port {PORT}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level=LOG_LEVEL.lower()
    )