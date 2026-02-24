"""
Mock FastAPI Application with Intentional Crash Behavior.

This FastAPI app simulates a production service with a bug that causes crashes
when a specific header is present. This is used to test the Self-Healing SRE Agent's
ability to detect, analyze, and fix issues automatically.

The bug: When the request header "X-Trigger-Bug" is set to "true", the endpoint
attempts to access a dictionary key that doesn't exist, causing a KeyError.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn


# Configure logging to write to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_logs.txt"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SRE Demo Service",
    description="A mock service with an intentional bug for testing self-healing",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    timestamp: str
    service: str


class DataResponse(BaseModel):
    """Response model for successful data requests."""
    data: dict
    message: str
    timestamp: str


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed with error: {str(e)}", exc_info=True)
        raise


@app.get("/", response_model=dict)
async def root():
    """Root endpoint returning basic service information."""
    return {
        "service": "SRE Demo Service",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "data": "/api/data"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service health status. Always returns healthy unless
    the service is completely down.
    """
    logger.info("Health check requested")
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        service="SRE Demo Service"
    )


@app.get("/api/data", response_model=DataResponse)
async def get_data(
    request: Request,
    x_trigger_bug: Optional[str] = Header(None, alias="X-Trigger-Bug")
):
    """
    Main data endpoint with intentional bug.
    
    This endpoint demonstrates a common programming error: accessing a dictionary
    key that doesn't exist without proper error handling.
    
    BUG: When X-Trigger-Bug header is "true", attempts to access user_config["api_key"]
         which doesn't exist, causing a KeyError crash.
    
    Args:
        request: The FastAPI request object
        x_trigger_bug: Optional header to trigger the bug (default: None)
    
    Returns:
        DataResponse with user data and message
    
    Raises:
        KeyError: When the bug is triggered and user_config["api_key"] is accessed
    """
    logger.info(f"Data endpoint called with X-Trigger-Bug={x_trigger_bug}")
    
    # Simulate user configuration data
    user_config = {
        "user_id": 12345,
        "username": "demo_user",
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
        # Note: "api_key" is intentionally missing!
    }
    
    # THE BUG: This code assumes api_key exists, but it doesn't!
    # When the header is set, this will crash with KeyError
    if x_trigger_bug and x_trigger_bug.lower() == "true":
        logger.warning("Bug trigger detected! Attempting to access missing api_key...")
        # This line will crash because "api_key" doesn't exist in user_config
        api_key = user_config["api_key"]  # KeyError!
        logger.info(f"Using API key: {api_key}")
    
    # Normal response when bug is not triggered
    return DataResponse(
        data=user_config,
        message="Data retrieved successfully",
        timestamp=datetime.utcnow().isoformat()
    )


@app.exception_handler(KeyError)
async def keyerror_exception_handler(request: Request, exc: KeyError):
    """
    Custom exception handler for KeyError.
    
    This logs the error in detail and returns a 500 error response.
    The self-healing agent will detect this error in the logs.
    """
    error_details = {
        "error": "Internal Server Error",
        "error_type": "KeyError",
        "missing_key": str(exc),
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.error(
        f"CRITICAL ERROR - KeyError in {request.url.path}: "
        f"Missing key {exc}. This error should be fixed!",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=error_details
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unexpected errors."""
    logger.error(
        f"Unexpected error in {request.url.path}: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    logger.info("Starting SRE Demo Service...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
