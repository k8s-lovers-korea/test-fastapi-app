import asyncio
import logging
import threading
import time
import uuid
from typing import Dict, List, Optional, Union
from contextlib import asynccontextmanager
from datetime import datetime
import os
import platform
import psutil

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
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

# Custom Prometheus Metrics
items_created = Counter('items_created_total', 'Total number of items created')
items_deleted = Counter('items_deleted_total', 'Total number of items deleted')
items_updated = Counter('items_updated_total', 'Total number of items updated')
request_duration = Histogram('request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
active_items_gauge = Gauge('active_items_count', 'Number of active items in storage')
blocked_threads_gauge = Gauge('blocked_threads_count', 'Number of currently blocked threads')

# Custom Exception Classes
class ItemNotFoundError(HTTPException):
    def __init__(self, item_id: str):
        super().__init__(status_code=404, detail=f"Item with id {item_id} not found")

class ValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=400, detail=message)

# Pydantic models
class Item(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    in_stock: bool = Field(True, description="Whether item is in stock")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default_factory=list, description="Item tags for categorization")

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    in_stock: Optional[bool] = None
    tags: Optional[List[str]] = None

class ItemSearch(BaseModel):
    query: Optional[str] = Field(None, description="Search query for name or description")
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None
    tags: Optional[List[str]] = None

class BulkItemCreate(BaseModel):
    items: List[Item] = Field(..., min_length=1, max_length=100)

class BulkItemUpdate(BaseModel):
    updates: Dict[str, ItemUpdate] = Field(..., min_length=1, max_length=100)

class HealthStatus(BaseModel):
    status: str
    timestamp: float
    details: Dict[str, Union[int, str, bool, float]]
    system_info: Dict[str, Union[str, float]]

class SystemInfo(BaseModel):
    python_version: str
    platform: str
    cpu_count: int
    memory_total: int
    memory_available: int
    disk_usage: Dict[str, Union[int, float]]

# In-memory storage with thread safety
items_storage: Dict[str, Item] = {}
storage_lock = threading.RLock()
blocking_lock = threading.Lock()

# Global state for simulating blocking
is_blocked = False
blocked_threads = set()

# Application startup time
startup_time = datetime.now()

def get_system_info() -> Dict[str, Union[str, float]]:
    """Get system information for health checks"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_mb": round(memory.total / 1024 / 1024, 2),
            "memory_available_mb": round(memory.available / 1024 / 1024, 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "disk_percent": round((disk.used / disk.total) * 100, 2)
        }
    except Exception as e:
        logger.warning(f"Failed to get system info: {e}")
        return {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "error": str(e)
        }

def search_items(search_params: ItemSearch) -> List[Item]:
    """Search items based on criteria"""
    results = []
    
    with storage_lock:
        for item in items_storage.values():
            # Text search in name and description
            if search_params.query:
                query_lower = search_params.query.lower()
                if (query_lower not in item.name.lower() and 
                    (not item.description or query_lower not in item.description.lower())):
                    continue
            
            # Price range filter
            if search_params.min_price is not None and item.price < search_params.min_price:
                continue
            if search_params.max_price is not None and item.price > search_params.max_price:
                continue
                
            # Stock status filter
            if search_params.in_stock is not None and item.in_stock != search_params.in_stock:
                continue
                
            # Tags filter
            if search_params.tags:
                if not item.tags or not any(tag in item.tags for tag in search_params.tags):
                    continue
                    
            results.append(item)
    
    return results

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    logger.info("Enhanced FastAPI application starting up...")
    logger.info(f"Application version: 2.0.0")
    logger.info(f"Startup time: {startup_time.isoformat()}")
    yield
    logger.info("Enhanced FastAPI application shutting down...")

# Create FastAPI app with enhanced configuration
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Enhanced FastAPI Test Application",
        version="2.0.0",
        description="""
        A comprehensive FastAPI application demonstrating:
        
        * **CRUD Operations**: Complete item management with search and filtering
        * **Bulk Operations**: Batch create and update operations
        * **Thread Simulation**: Blocking behavior and timeout scenarios
        * **Observability**: Distributed tracing, metrics, and comprehensive logging
        * **Actuator Endpoints**: Health checks, metrics, and system information
        * **Search & Filter**: Advanced item search capabilities
        
        Built with production-ready patterns including thread safety, error handling, and monitoring.
        """,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="Enhanced FastAPI Test Application",
    description="A comprehensive FastAPI app with CRUD, search, bulk operations, tracing, and metrics",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.openapi = custom_openapi

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
    method = request.method
    url_path = request.url.path
    
    # Log incoming request
    logger.info(f"Incoming request: {method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Create trace span
    with tracer.start_as_current_span(f"{method} {url_path}") as span:
        span.set_attribute("http.method", method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Request processed in {process_time:.4f}s - Status: {response.status_code}")
        
        span.set_attribute("http.status_code", response.status_code)
        span.set_attribute("duration", process_time)
        
        # Update Prometheus metrics
        request_duration.labels(method=method, endpoint=url_path).observe(process_time)
        
    return response

# CRUD Operations
@app.post("/items/", response_model=Item, tags=["Items"], summary="Create a new item")
async def create_item(item: Item):
    """Create a new item with automatic ID generation and timestamps"""
    with tracer.start_as_current_span("create_item"):
        logger.info(f"Creating new item: {item.name}")
        
        with storage_lock:
            item_id = str(uuid.uuid4())
            item.id = item_id
            item.created_at = datetime.now()
            item.updated_at = datetime.now()
            items_storage[item_id] = item
            
            # Update metrics
            items_created.inc()
            active_items_gauge.set(len(items_storage))
            
        logger.info(f"Item created with ID: {item_id}")
        return item

@app.post("/items/bulk", response_model=List[Item], tags=["Items"], summary="Create multiple items")
async def create_items_bulk(bulk_request: BulkItemCreate):
    """Create multiple items in a single operation"""
    with tracer.start_as_current_span("create_items_bulk") as span:
        span.set_attribute("items.count", len(bulk_request.items))
        logger.info(f"Creating {len(bulk_request.items)} items in bulk")
        
        created_items = []
        with storage_lock:
            for item in bulk_request.items:
                item_id = str(uuid.uuid4())
                item.id = item_id
                item.created_at = datetime.now()
                item.updated_at = datetime.now()
                items_storage[item_id] = item
                created_items.append(item)
                items_created.inc()
            
            active_items_gauge.set(len(items_storage))
            
        logger.info(f"Bulk created {len(created_items)} items")
        return created_items

@app.get("/items/", response_model=List[Item], tags=["Items"], summary="Get all items")
async def get_items(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """Get all items with pagination support"""
    with tracer.start_as_current_span("get_all_items") as span:
        logger.info(f"Retrieving items with limit={limit}, offset={offset}")
        
        with storage_lock:
            all_items = list(items_storage.values())
            items = all_items[offset:offset + limit]
            
        span.set_attribute("items.total", len(all_items))
        span.set_attribute("items.returned", len(items))
        logger.info(f"Retrieved {len(items)} items (total: {len(all_items)})")
        return items

@app.post("/items/search", response_model=List[Item], tags=["Items"], summary="Search items")
async def search_items_endpoint(search_params: ItemSearch):
    """Search items based on various criteria"""
    with tracer.start_as_current_span("search_items") as span:
        logger.info(f"Searching items with criteria: {search_params}")
        
        results = search_items(search_params)
        
        span.set_attribute("search.results_count", len(results))
        logger.info(f"Search returned {len(results)} results")
        return results

@app.get("/items/{item_id}", response_model=Item, tags=["Items"], summary="Get item by ID")
async def get_item(item_id: str):
    """Get a specific item by ID"""
    with tracer.start_as_current_span("get_item") as span:
        span.set_attribute("item.id", item_id)
        logger.info(f"Retrieving item: {item_id}")
        
        with storage_lock:
            if item_id not in items_storage:
                logger.warning(f"Item not found: {item_id}")
                raise ItemNotFoundError(item_id)
            
            item = items_storage[item_id]
            
        logger.info(f"Item retrieved: {item.name}")
        return item

@app.put("/items/{item_id}", response_model=Item, tags=["Items"], summary="Update item")
async def update_item(item_id: str, item_update: ItemUpdate):
    """Update an existing item"""
    with tracer.start_as_current_span("update_item") as span:
        span.set_attribute("item.id", item_id)
        logger.info(f"Updating item: {item_id}")
        
        with storage_lock:
            if item_id not in items_storage:
                logger.warning(f"Item not found for update: {item_id}")
                raise ItemNotFoundError(item_id)
            
            existing_item = items_storage[item_id]
            
            # Update only provided fields
            update_data = item_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(existing_item, field):
                    setattr(existing_item, field, value)
            
            existing_item.updated_at = datetime.now()
            items_storage[item_id] = existing_item
            
            # Update metrics
            items_updated.inc()
            
        logger.info(f"Item updated: {item_id}")
        return existing_item

@app.put("/items/bulk-update", response_model=Dict[str, Item], tags=["Items"], summary="Update multiple items")
async def update_items_bulk(bulk_update: BulkItemUpdate):
    """Update multiple items in a single operation"""
    with tracer.start_as_current_span("update_items_bulk") as span:
        span.set_attribute("items.count", len(bulk_update.updates))
        logger.info(f"Bulk updating {len(bulk_update.updates)} items")
        
        updated_items = {}
        with storage_lock:
            for item_id, item_update in bulk_update.updates.items():
                if item_id not in items_storage:
                    logger.warning(f"Item not found for bulk update: {item_id}")
                    continue
                
                existing_item = items_storage[item_id]
                update_data = item_update.model_dump(exclude_unset=True)
                
                for field, value in update_data.items():
                    if hasattr(existing_item, field):
                        setattr(existing_item, field, value)
                
                existing_item.updated_at = datetime.now()
                items_storage[item_id] = existing_item
                updated_items[item_id] = existing_item
                items_updated.inc()
        
        logger.info(f"Bulk updated {len(updated_items)} items")
        return updated_items

@app.delete("/items/{item_id}", tags=["Items"], summary="Delete item")
async def delete_item(item_id: str):
    """Delete an item"""
    with tracer.start_as_current_span("delete_item") as span:
        span.set_attribute("item.id", item_id)
        logger.info(f"Deleting item: {item_id}")
        
        with storage_lock:
            if item_id not in items_storage:
                logger.warning(f"Item not found for deletion: {item_id}")
                raise ItemNotFoundError(item_id)
            
            deleted_item = items_storage.pop(item_id)
            
            # Update metrics
            items_deleted.inc()
            active_items_gauge.set(len(items_storage))
            
        logger.info(f"Item deleted: {item_id}")
        return {"message": f"Item {item_id} deleted successfully", "deleted_item": deleted_item}

@app.post("/items/delete", tags=["Items"], summary="Delete multiple items")
async def delete_items_bulk(item_ids: List[str]):
    """Delete multiple items in a single operation"""
    with tracer.start_as_current_span("delete_items_bulk") as span:
        span.set_attribute("items.count", len(item_ids))
        logger.info(f"Bulk deleting {len(item_ids)} items")
        
        deleted_items = {}
        not_found_ids = []
        
        with storage_lock:
            for item_id in item_ids:
                if item_id in items_storage:
                    deleted_items[item_id] = items_storage.pop(item_id)
                    items_deleted.inc()
                else:
                    not_found_ids.append(item_id)
            
            active_items_gauge.set(len(items_storage))
        
        result = {
            "message": f"Bulk delete completed",
            "deleted_count": len(deleted_items),
            "not_found_count": len(not_found_ids),
            "deleted_items": deleted_items
        }
        
        if not_found_ids:
            result["not_found_ids"] = not_found_ids
        
        logger.info(f"Bulk deleted {len(deleted_items)} items, {len(not_found_ids)} not found")
        return result

# Thread blocking simulation
@app.post("/simulate/block", tags=["Simulation"], summary="Simulate thread blocking")
async def simulate_blocking():
    """Simulate thread blocking behavior"""
    global is_blocked
    
    with tracer.start_as_current_span("simulate_blocking"):
        logger.info("Simulating thread blocking")
        
        def blocking_operation():
            thread_id = threading.current_thread().ident
            logger.info(f"Thread {thread_id} acquiring blocking lock")
            blocked_threads.add(thread_id)
            blocked_threads_gauge.set(len(blocked_threads))
            
            with blocking_lock:
                logger.info(f"Thread {thread_id} acquired lock, sleeping for 30 seconds")
                time.sleep(30)
                
            blocked_threads.discard(thread_id)
            blocked_threads_gauge.set(len(blocked_threads))
            logger.info(f"Thread {thread_id} released blocking lock")
        
        # Run blocking operation in background
        thread = threading.Thread(target=blocking_operation, name="BlockingSimulation")
        thread.start()
        
        return {
            "message": "Thread blocking simulation started", 
            "duration": "30 seconds",
            "thread_name": thread.name
        }

@app.get("/simulate/block/status", tags=["Simulation"], summary="Get blocking status")
async def get_blocking_status():
    """Get current blocking status"""
    with tracer.start_as_current_span("get_blocking_status"):
        return {
            "blocked_threads": list(blocked_threads),
            "blocked_count": len(blocked_threads),
            "lock_available": not blocking_lock.locked(),
            "active_threads": threading.active_count()
        }

# Timeout simulation
@app.get("/simulate/timeout/{duration}", tags=["Simulation"], summary="Simulate timeout")
async def simulate_timeout(duration: int):
    """Simulate timeout scenarios - duration in seconds"""
    with tracer.start_as_current_span("simulate_timeout") as span:
        span.set_attribute("timeout.duration", duration)
        logger.info(f"Starting timeout simulation for {duration} seconds")
        
        if duration > 300:  # Max 5 minutes for safety
            raise ValidationError("Maximum timeout duration is 300 seconds")
        
        start_time = time.time()
        await asyncio.sleep(duration)
        end_time = time.time()
        
        actual_duration = end_time - start_time
        logger.info(f"Timeout simulation completed. Requested: {duration}s, Actual: {actual_duration:.2f}s")
        
        return {
            "message": "Timeout simulation completed",
            "requested_duration": duration,
            "actual_duration": round(actual_duration, 2),
            "start_time": start_time,
            "end_time": end_time
        }

# Enhanced Actuator endpoints
@app.get("/actuator/health", response_model=HealthStatus, tags=["Actuator"], summary="Comprehensive health check")
async def health_check():
    """Enhanced health check with system information"""
    with tracer.start_as_current_span("health_check"):
        logger.info("Health check requested")
        
        system_info = get_system_info()
        uptime = (datetime.now() - startup_time).total_seconds()
        
        return HealthStatus(
            status="UP",
            timestamp=time.time(),
            details={
                "items_count": len(items_storage),
                "blocked_threads": len(blocked_threads),
                "uptime_seconds": round(uptime, 2),
                "storage_lock_available": not storage_lock._is_owned(),
                "blocking_lock_available": not blocking_lock.locked()
            },
            system_info=system_info
        )

@app.get("/actuator/info", tags=["Actuator"], summary="Application information")
async def app_info():
    """Detailed application information"""
    with tracer.start_as_current_span("app_info"):
        uptime = (datetime.now() - startup_time).total_seconds()
        return {
            "app": {
                "name": "enhanced-fastapi-test-app",
                "version": "2.0.0",
                "description": "Enhanced FastAPI application with CRUD, search, bulk operations, tracing, and metrics"
            },
            "build": {
                "time": startup_time.isoformat(),
                "uptime_seconds": round(uptime, 2)
            },
            "features": [
                "CRUD Operations",
                "Bulk Operations", 
                "Search & Filtering",
                "Thread Simulation",
                "Distributed Tracing",
                "Prometheus Metrics",
                "Health Monitoring",
                "OpenAPI Documentation"
            ],
            "endpoints": {
                "items": "/items/",
                "bulk_create": "/items/bulk",
                "search": "/items/search", 
                "health": "/actuator/health",
                "metrics": "/metrics",
                "docs": "/docs"
            }
        }

@app.get("/actuator/env", tags=["Actuator"], summary="Environment information")
async def environment_info():
    """Environment and configuration information"""
    with tracer.start_as_current_span("environment_info"):
        return {
            "environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "hostname": platform.node(),
            },
            "configuration": {
                "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
                "log_level": logging.getLogger().level,
                "otlp_endpoint": os.getenv("OTLP_ENDPOINT", "http://localhost:4317"),
                "jaeger_host": os.getenv("JAEGER_HOST", "localhost")
            },
            "runtime": {
                "process_id": os.getpid(),
                "thread_count": threading.active_count(),
                "main_thread": threading.main_thread().name
            }
        }

@app.post("/actuator/restart", tags=["Actuator"], summary="Trigger restart simulation")
async def trigger_restart(background_tasks: BackgroundTasks):
    """Trigger application restart simulation"""
    with tracer.start_as_current_span("trigger_restart"):
        logger.warning("Application restart triggered!")
        
        def restart_simulation():
            logger.info("Simulating application restart...")
            time.sleep(2)
            logger.info("Application restart simulation completed")
        
        background_tasks.add_task(restart_simulation)
        
        return {
            "message": "Application restart initiated",
            "timestamp": time.time(),
            "estimated_downtime": "2 seconds"
        }

@app.get("/actuator/metrics", tags=["Actuator"], summary="Application metrics")
async def get_custom_metrics():
    """Enhanced custom metrics endpoint"""
    with tracer.start_as_current_span("get_metrics"):
        uptime = (datetime.now() - startup_time).total_seconds()
        
        # Update gauges
        active_items_gauge.set(len(items_storage))
        blocked_threads_gauge.set(len(blocked_threads))
        
        return {
            "application": {
                "uptime_seconds": round(uptime, 2),
                "startup_time": startup_time.isoformat()
            },
            "items": {
                "total_count": len(items_storage),
                "created_total": int(items_created._value._value),
                "updated_total": int(items_updated._value._value),
                "deleted_total": int(items_deleted._value._value)
            },
            "threading": {
                "blocked_threads_count": len(blocked_threads),
                "active_threads_count": threading.active_count(),
                "storage_lock_status": "locked" if storage_lock._is_owned() else "available",
                "blocking_lock_status": "locked" if blocking_lock.locked() else "available"
            },
            "system": get_system_info(),
            "timestamp": time.time()
        }

@app.get("/actuator/threads", tags=["Actuator"], summary="Thread information")
async def get_thread_info():
    """Get detailed thread information"""
    with tracer.start_as_current_span("get_thread_info"):
        threads_info = []
        for thread in threading.enumerate():
            threads_info.append({
                "name": thread.name,
                "ident": thread.ident,
                "is_alive": thread.is_alive(),
                "daemon": thread.daemon,
                "is_main": thread == threading.main_thread()
            })
        
        return {
            "active_count": threading.active_count(),
            "blocked_count": len(blocked_threads),
            "main_thread": threading.main_thread().name,
            "threads": threads_info,
            "locks": {
                "storage_lock_owner": storage_lock._owner if hasattr(storage_lock, '_owner') else None,
                "blocking_lock_locked": blocking_lock.locked()
            }
        }

# Root endpoint
@app.get("/", tags=["General"], summary="Application information")
async def root():
    """Enhanced root endpoint with comprehensive application information"""
    with tracer.start_as_current_span("root"):
        logger.info("Root endpoint accessed")
        uptime = (datetime.now() - startup_time).total_seconds()
        
        return {
            "message": "Enhanced FastAPI Test Application",
            "version": "2.0.0",
            "uptime_seconds": round(uptime, 2),
            "startup_time": startup_time.isoformat(),
            "features": {
                "crud_operations": "Full CRUD with validation and timestamps",
                "bulk_operations": "Batch create, update, and delete",
                "search_filtering": "Advanced search with multiple criteria",
                "thread_simulation": "Blocking and timeout scenarios",
                "observability": "Tracing, metrics, and comprehensive logging",
                "actuator_endpoints": "Health, metrics, and system information"
            },
            "endpoints": {
                "documentation": "/docs",
                "openapi": "/openapi.json",
                "items": {
                    "crud": "/items/",
                    "bulk_create": "/items/bulk",
                    "bulk_update": "/items/bulk-update",
                    "bulk_delete": "/items/delete",
                    "search": "/items/search"
                },
                "simulation": {
                    "block": "/simulate/block",
                    "block_status": "/simulate/block/status",
                    "timeout": "/simulate/timeout/{duration}"
                },
                "actuator": {
                    "health": "/actuator/health",
                    "info": "/actuator/info",
                    "env": "/actuator/env",
                    "metrics": "/actuator/metrics",
                    "threads": "/actuator/threads",
                    "restart": "/actuator/restart"
                },
                "monitoring": {
                    "prometheus": "/metrics"
                }
            },
            "statistics": {
                "items_count": len(items_storage),
                "blocked_threads": len(blocked_threads),
                "active_threads": threading.active_count()
            }
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)