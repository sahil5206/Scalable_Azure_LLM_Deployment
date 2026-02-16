"""
Health check endpoint for LLM Worker Service.

Provides health and readiness checks for Kubernetes.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Worker Health Check")


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "llm-worker"}
    )


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns ready status if the worker is ready to process requests.
    This should check if model is loaded and Kafka connections are established.
    """
    # TODO: Add actual readiness checks
    # - Model loaded
    # - Kafka consumer connected
    # - Kafka producer connected
    return JSONResponse(
        status_code=200,
        content={"status": "ready", "service": "llm-worker"}
    )


@app.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Returns alive status if the worker process is running.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "alive", "service": "llm-worker"}
    )
