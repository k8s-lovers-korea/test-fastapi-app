"""
Simple FastAPI application with OpenTelemetry auto-instrumentation.
"""

import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# Import our modules
from config import Config
from app.core.observability import setup_telemetry, instrument_fastapi_app
from app.core.storage import startup_time
from app.routers import items, simulation, actuator, entities, test_scenarios

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    logger.info(f"{Config.APP_NAME} starting up...")
    logger.info(f"Application version: {Config.APP_VERSION}")
    logger.info(f"Startup time: {startup_time.isoformat()}")

    # Setup OpenTelemetry
    setup_telemetry()

    yield
    logger.info(f"{Config.APP_NAME} shutting down...")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=Config.APP_NAME,
        version=Config.APP_VERSION,
        description=Config.get_openapi_description(),
        routes=app.routes,
    )
    openapi_schema["info"].update(Config.get_openapi_info())
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create FastAPI app with enhanced configuration
app = FastAPI(
    title=Config.APP_NAME,
    description=Config.APP_DESCRIPTION,
    version=Config.APP_VERSION,
    lifespan=lifespan,
    docs_url=Config.DOCS_URL,
    redoc_url=Config.REDOC_URL,
    openapi_url=Config.OPENAPI_URL,
)

app.openapi = custom_openapi

# Instrument FastAPI app
instrument_fastapi_app(app)

# Include routers
app.include_router(items.router)
app.include_router(simulation.router)
app.include_router(actuator.router)
app.include_router(entities.router)
app.include_router(test_scenarios.router)


# Root endpoint
@app.get("/", tags=["General"], summary="Application information")
async def root():
    """Simple root endpoint"""
    logger.info("Root endpoint accessed")

    return {
        "message": "Simple FastAPI Test Application",
        "version": "1.0.0",
        "features": {
            "crud_operations": "Full CRUD operations",
            "bulk_operations": "Batch create, update, and delete",
            "search_filtering": "Search with multiple criteria",
            "thread_simulation": "Blocking and timeout scenarios",
        },
        "endpoints": {
            "documentation": "/docs",
            "openapi": "/openapi.json",
            "items": {
                "crud": "/items/",
                "bulk_create": "/items/bulk",
                "bulk_update": "/items/bulk-update",
                "bulk_delete": "/items/delete",
                "search": "/items/search",
            },
            "entities": {
                "crud": "/api/entities/",
                "get_by_id": "/api/entities/{id}",
                "search": "/api/entities/search?name={name}",
            },
            "test_scenarios": {
                "health": "/api/test/health",
                "block_thread": "/api/test/block-thread?seconds={n}",
                "hang": "/api/test/hang?seconds={n}",
                "cpu_intensive": "/api/test/cpu-intensive?seconds={n}",
                "thread_status": "/api/test/thread-status",
            },
            "simulation": {
                "block": "/simulate/block",
                "block_status": "/simulate/block/status",
                "timeout": "/simulate/timeout/{duration}",
            },
            "actuator": {
                "health": "/actuator/health",
                "info": "/actuator/info",
                "env": "/actuator/env",
                "threads": "/actuator/threads",
                "restart": "/actuator/restart",
            },
        },
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=Config.RELOAD)
