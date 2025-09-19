import asyncio
import logging
import threading
import time
import uuid
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenTelemetry setup
resource = Resource.create({"service.name": "fastapi-test-app"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Configure OTLP exporter (can be switched to Jaeger)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Pydantic models
class Item(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    in_stock: bool = True

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None

# In-memory storage with thread safety
items_storage: Dict[str, Item] = {}
storage_lock = threading.RLock()
blocking_lock = threading.Lock()

# Global state for simulating blocking
is_blocked = False
blocked_threads = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    logger.info("FastAPI application starting up...")
    yield
    logger.info("FastAPI application shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Test FastAPI Application",
    description="A FastAPI app with CRUD operations, thread simulation, tracing, and metrics",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Setup Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app)
instrumentator.expose(app)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Create trace span
    with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Request processed in {process_time:.4f}s - Status: {response.status_code}")
        
        span.set_attribute("http.status_code", response.status_code)
        span.set_attribute("duration", process_time)
        
    return response

# CRUD Operations
@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    """Create a new item"""
    with tracer.start_as_current_span("create_item"):
        logger.info(f"Creating new item: {item.name}")
        
        with storage_lock:
            item_id = str(uuid.uuid4())
            item.id = item_id
            items_storage[item_id] = item
            
        logger.info(f"Item created with ID: {item_id}")
        return item

@app.get("/items/", response_model=List[Item])
async def get_items():
    """Get all items"""
    with tracer.start_as_current_span("get_all_items"):
        logger.info("Retrieving all items")
        
        with storage_lock:
            items = list(items_storage.values())
            
        logger.info(f"Retrieved {len(items)} items")
        return items

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    """Get a specific item by ID"""
    with tracer.start_as_current_span("get_item") as span:
        span.set_attribute("item.id", item_id)
        logger.info(f"Retrieving item: {item_id}")
        
        with storage_lock:
            if item_id not in items_storage:
                logger.warning(f"Item not found: {item_id}")
                raise HTTPException(status_code=404, detail="Item not found")
            
            item = items_storage[item_id]
            
        logger.info(f"Item retrieved: {item.name}")
        return item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item_update: ItemUpdate):
    """Update an existing item"""
    with tracer.start_as_current_span("update_item") as span:
        span.set_attribute("item.id", item_id)
        logger.info(f"Updating item: {item_id}")
        
        with storage_lock:
            if item_id not in items_storage:
                logger.warning(f"Item not found for update: {item_id}")
                raise HTTPException(status_code=404, detail="Item not found")
            
            existing_item = items_storage[item_id]
            
            # Update only provided fields
            update_data = item_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(existing_item, field):
                    setattr(existing_item, field, value)
                    
            items_storage[item_id] = existing_item
            
        logger.info(f"Item updated: {item_id}")
        return existing_item

@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """Delete an item"""
    with tracer.start_as_current_span("delete_item") as span:
        span.set_attribute("item.id", item_id)
        logger.info(f"Deleting item: {item_id}")
        
        with storage_lock:
            if item_id not in items_storage:
                logger.warning(f"Item not found for deletion: {item_id}")
                raise HTTPException(status_code=404, detail="Item not found")
            
            deleted_item = items_storage.pop(item_id)
            
        logger.info(f"Item deleted: {item_id}")
        return {"message": f"Item {item_id} deleted successfully"}

# Thread blocking simulation
@app.post("/simulate/block")
async def simulate_blocking():
    """Simulate thread blocking behavior"""
    global is_blocked
    
    with tracer.start_as_current_span("simulate_blocking"):
        logger.info("Simulating thread blocking")
        
        def blocking_operation():
            thread_id = threading.current_thread().ident
            logger.info(f"Thread {thread_id} acquiring blocking lock")
            blocked_threads.add(thread_id)
            
            with blocking_lock:
                logger.info(f"Thread {thread_id} acquired lock, sleeping for 30 seconds")
                time.sleep(30)
                
            blocked_threads.discard(thread_id)
            logger.info(f"Thread {thread_id} released blocking lock")
        
        # Run blocking operation in background
        thread = threading.Thread(target=blocking_operation)
        thread.start()
        
        return {"message": "Thread blocking simulation started", "duration": "30 seconds"}

@app.get("/simulate/block/status")
async def get_blocking_status():
    """Get current blocking status"""
    with tracer.start_as_current_span("get_blocking_status"):
        return {
            "blocked_threads": list(blocked_threads),
            "lock_available": not blocking_lock.locked()
        }

# Timeout simulation
@app.get("/simulate/timeout/{duration}")
async def simulate_timeout(duration: int):
    """Simulate timeout scenarios - duration in seconds"""
    with tracer.start_as_current_span("simulate_timeout") as span:
        span.set_attribute("timeout.duration", duration)
        logger.info(f"Starting timeout simulation for {duration} seconds")
        
        if duration > 300:  # Max 5 minutes for safety
            raise HTTPException(status_code=400, detail="Maximum timeout duration is 300 seconds")
        
        start_time = time.time()
        await asyncio.sleep(duration)
        end_time = time.time()
        
        actual_duration = end_time - start_time
        logger.info(f"Timeout simulation completed. Requested: {duration}s, Actual: {actual_duration:.2f}s")
        
        return {
            "message": "Timeout simulation completed",
            "requested_duration": duration,
            "actual_duration": round(actual_duration, 2)
        }

# Actuator endpoints
@app.get("/actuator/health")
async def health_check():
    """Health check endpoint"""
    with tracer.start_as_current_span("health_check"):
        logger.info("Health check requested")
        
        return {
            "status": "UP",
            "timestamp": time.time(),
            "details": {
                "items_count": len(items_storage),
                "blocked_threads": len(blocked_threads)
            }
        }

@app.get("/actuator/info")
async def app_info():
    """Application information"""
    with tracer.start_as_current_span("app_info"):
        return {
            "app": {
                "name": "test-fastapi-app",
                "version": "1.0.0",
                "description": "FastAPI application with CRUD, tracing, and metrics"
            },
            "build": {
                "time": time.time()
            }
        }

@app.post("/actuator/restart")
async def trigger_restart(background_tasks: BackgroundTasks):
    """Trigger application restart (simulation)"""
    with tracer.start_as_current_span("trigger_restart"):
        logger.warning("Application restart triggered!")
        
        def restart_simulation():
            logger.info("Simulating application restart...")
            time.sleep(2)
            logger.info("Application restart simulation completed")
        
        background_tasks.add_task(restart_simulation)
        
        return {
            "message": "Application restart initiated",
            "timestamp": time.time()
        }

@app.get("/actuator/metrics")
async def get_custom_metrics():
    """Custom metrics endpoint"""
    with tracer.start_as_current_span("get_metrics"):
        return {
            "items_total": len(items_storage),
            "blocked_threads_count": len(blocked_threads),
            "lock_status": "locked" if blocking_lock.locked() else "available",
            "timestamp": time.time()
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    with tracer.start_as_current_span("root"):
        logger.info("Root endpoint accessed")
        return {
            "message": "FastAPI Test Application",
            "version": "1.0.0",
            "endpoints": {
                "items": "/items/",
                "health": "/actuator/health",
                "metrics": "/metrics",
                "simulate_blocking": "/simulate/block",
                "simulate_timeout": "/simulate/timeout/{duration}",
                "restart": "/actuator/restart"
            }
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)