"""
Web frontend API server for LLM inference.

Provides REST API and serves web UI for interacting with LLM models.
"""
import asyncio
import json
import time
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi import Request as FastAPIRequest
from pathlib import Path
from pydantic import BaseModel
from confluent_kafka import Producer, Consumer, KafkaError
from web.config import config
from web.azure_ml_client import get_azure_ml_client, AzureMLEndpointClient
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LLM Inference API",
    description="Web API for LLM model inference via Kafka",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"

# Kafka producer (shared instance)
producer: Optional[Producer] = None


class InferenceRequest(BaseModel):
    """Request model for inference."""
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class InferenceResponse(BaseModel):
    """Response model for inference."""
    request_id: str
    status: str
    generated_text: Optional[str] = None
    error: Optional[str] = None
    tokens_generated: Optional[int] = None
    response_time: Optional[float] = None


def get_producer() -> Producer:
    """Get or create Kafka producer."""
    global producer
    if producer is None:
        producer = Producer({
            'bootstrap.servers': config.kafka_bootstrap_servers,
            'client.id': 'web-frontend-producer'
        })
    return producer


async def send_kafka_request(
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> str:
    """
    Send inference request to Kafka.
    
    Returns:
        Request ID
    """
    request_id = f"web-{uuid.uuid4().hex[:8]}"
    
    request_message = {
        "request_id": request_id,
        "prompt": prompt,
        "max_tokens": max_tokens or config.max_tokens,
        "temperature": temperature or config.temperature,
        "timestamp": time.time()
    }
    
    producer = get_producer()
    
    try:
        producer.produce(
            config.kafka_request_topic,
            key=request_id,
            value=json.dumps(request_message)
        )
        producer.flush(timeout=5)
        logger.info(f"Request sent: {request_id}")
        return request_id
    except Exception as e:
        logger.error(f"Error sending request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send request: {str(e)}")


async def wait_for_response(request_id: str, timeout: int = None) -> dict:
    """
    Wait for response from Kafka.
    
    Args:
        request_id: Request ID to wait for
        timeout: Timeout in seconds
    
    Returns:
        Response dictionary
    """
    timeout = timeout or config.request_timeout_seconds
    start_time = time.time()
    
    # Create consumer for this request
    consumer = Consumer({
        'bootstrap.servers': config.kafka_bootstrap_servers,
        'group.id': f'{config.kafka_consumer_group}-{request_id}',
        'auto.offset.reset': 'latest',
        'enable.auto.commit': False
    })
    consumer.subscribe([config.kafka_response_topic])
    
    try:
        while time.time() - start_time < timeout:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    break
            
            try:
                response_data = json.loads(msg.value().decode('utf-8'))
                
                # Check if this is our response
                if response_data.get("request_id") == request_id:
                    consumer.close()
                    return response_data
            except Exception as e:
                logger.error(f"Error parsing response: {e}")
                continue
        
        consumer.close()
        raise HTTPException(
            status_code=504,
            detail=f"Timeout waiting for response: {request_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        consumer.close()
        raise HTTPException(status_code=500, detail=f"Error waiting for response: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    html_file = TEMPLATE_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return HTMLResponse(content="<h1>Web UI not found</h1>", status_code=404)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "llm-web-frontend"}


@app.post("/api/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """
    Send inference request and wait for response.
    
    This endpoint can use either:
    1. Azure ML managed endpoint (if configured and available)
    2. Kafka-based worker service (fallback/default)
    """
    start_time = time.time()
    
    # Try Azure ML endpoint first (if available)
    azure_ml_client = get_azure_ml_client()
    if azure_ml_client and azure_ml_client.is_available():
        try:
            logger.info("Using Azure ML managed endpoint for inference")
            response_data = azure_ml_client.infer(
                prompt=request.prompt,
                max_tokens=request.max_tokens or config.max_tokens,
                temperature=request.temperature or config.temperature
            )
            
            response_time = time.time() - start_time
            
            return InferenceResponse(
                request_id=f"aml-{uuid.uuid4().hex[:8]}",
                status=response_data.get("status", "success"),
                generated_text=response_data.get("generated_text", ""),
                tokens_generated=response_data.get("tokens_generated"),
                response_time=round(response_time, 2),
                error=response_data.get("error")
            )
        except Exception as e:
            logger.warning(f"Azure ML endpoint failed, falling back to Kafka: {e}")
            # Fall through to Kafka-based inference
    
    # Fallback to Kafka-based inference
    try:
        logger.info("Using Kafka-based worker service for inference")
        # Send request to Kafka
        request_id = await send_kafka_request(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Wait for response
        response_data = await wait_for_response(request_id)
        
        response_time = time.time() - start_time
        
        # Format response
        return InferenceResponse(
            request_id=request_id,
            status=response_data.get("status", "unknown"),
            generated_text=response_data.get("generated_text", ""),
            tokens_generated=response_data.get("tokens_generated"),
            response_time=round(response_time, 2),
            error=response_data.get("error")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in inference endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/inference/async")
async def inference_async(request: InferenceRequest):
    """
    Send inference request asynchronously (fire and forget).
    
    Returns request ID immediately. Client should poll for results.
    """
    try:
        request_id = await send_kafka_request(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return {"request_id": request_id, "status": "submitted"}
    except Exception as e:
        logger.error(f"Error in async inference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inference/{request_id}")
async def get_inference_result(request_id: str):
    """
    Get inference result by request ID (for async requests).
    """
    try:
        response_data = await wait_for_response(request_id, timeout=5)
        return response_data
    except HTTPException as e:
        if e.status_code == 504:
            return {"status": "pending", "request_id": request_id}
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global producer
    if producer:
        producer.flush()
        producer = None
    logger.info("Web frontend shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.main:app",
        host=config.host,
        port=config.port,
        reload=True
    )
