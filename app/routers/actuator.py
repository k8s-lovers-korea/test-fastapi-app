"""
Actuator endpoints for health checks and monitoring.
"""

import logging
import os
import time
import threading
import platform
import psutil
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks

from app.models import HealthStatus
from app.core.storage import items_storage, blocked_threads, startup_time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actuator", tags=["💊 Actuator (FastAPI Internal)"])


@router.get("/health", response_model=HealthStatus, summary="Health check endpoint")
async def health():
    """💊 **FastAPI Internal**: Comprehensive health check with detailed status information from the FastAPI application itself."""
    logger.info("Health check requested")

    # Check system health indicators
    memory_info = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    disk_info = psutil.disk_usage("/")

    # Application-specific health checks
    items_count = len(items_storage)
    blocked_count = len(blocked_threads)
    uptime = (datetime.now() - startup_time).total_seconds()

    # Determine overall status
    status = "UP"
    details = {}

    # Memory check (warn if > 80%, critical if > 90%)
    if memory_info.percent > 90:
        status = "DOWN"
        details["memory"] = {"status": "CRITICAL", "usage_percent": memory_info.percent}
    elif memory_info.percent > 80:
        details["memory"] = {"status": "WARNING", "usage_percent": memory_info.percent}
    else:
        details["memory"] = {"status": "UP", "usage_percent": memory_info.percent}

    # CPU check (warn if > 85%, critical if > 95%)
    if cpu_percent > 95:
        status = "DOWN"
        details["cpu"] = {"status": "CRITICAL", "usage_percent": cpu_percent}
    elif cpu_percent > 85:
        details["cpu"] = {"status": "WARNING", "usage_percent": cpu_percent}
    else:
        details["cpu"] = {"status": "UP", "usage_percent": cpu_percent}

    # Disk check (warn if > 85%, critical if > 95%)
    disk_percent = (disk_info.used / disk_info.total) * 100
    if disk_percent > 95:
        status = "DOWN"
        details["disk"] = {"status": "CRITICAL", "usage_percent": disk_percent}
    elif disk_percent > 85:
        details["disk"] = {"status": "WARNING", "usage_percent": disk_percent}
    else:
        details["disk"] = {"status": "UP", "usage_percent": disk_percent}

    # Application checks
    details["application"] = {
        "status": "UP",
        "items_count": items_count,
        "blocked_threads": blocked_count,
        "uptime_seconds": round(uptime, 2),
    }

    # System info for the health status
    system_info = {
        "python_version": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()}",
        "cpu_count": psutil.cpu_count(),
        "memory_total": memory_info.total,
        "memory_available": memory_info.available,
    }

    return HealthStatus(
        status=status,
        timestamp=datetime.now().timestamp(),
        details=details,
        system_info=system_info,
    )


@router.get("/info", summary="Application information")
async def info():
    """Get detailed application and system information"""
    logger.info("Info endpoint accessed")

    uptime = (datetime.now() - startup_time).total_seconds()

    return {
        "application": {
            "name": "FastAPI Test Application",
            "version": "1.0.0",
            "description": "Simple FastAPI application for testing",
            "uptime_seconds": round(uptime, 2),
            "startup_time": startup_time.isoformat(),
        },
        "system": {
            "python_version": platform.python_version(),
            "platform": f"{platform.system()} {platform.release()}",
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
        },
        "runtime": {
            "process_id": os.getpid(),
            "thread_count": threading.active_count(),
            "memory_usage_mb": round(
                psutil.Process().memory_info().rss / 1024 / 1024, 2
            ),
        },
        "storage": {
            "items_count": len(items_storage),
            "blocked_threads_count": len(blocked_threads),
        },
    }


@router.get("/env", summary="Environment information")
async def env():
    """Get environment variables and configuration"""
    logger.info("Environment endpoint accessed")

    # Filter out sensitive environment variables
    sensitive_keys = {"password", "secret", "key", "token", "auth"}

    env_vars = {}
    for key, value in os.environ.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            env_vars[key] = "***HIDDEN***"
        else:
            env_vars[key] = value

    return {
        "environment_variables": env_vars,
        "python_path": os.environ.get("PYTHONPATH", "Not set"),
        "working_directory": os.getcwd(),
        "user": os.environ.get("USER", "Unknown"),
    }


@router.get("/threads", summary="Thread information")
async def threads():
    """Get information about running threads"""
    logger.info("Threads endpoint accessed")

    threads_info = []
    for thread in threading.enumerate():
        thread_info = {
            "name": thread.name,
            "thread_id": thread.ident,
            "is_alive": thread.is_alive(),
            "daemon": thread.daemon,
        }
        threads_info.append(thread_info)

    return {
        "total_threads": threading.active_count(),
        "blocked_threads_count": len(blocked_threads),
        "blocked_thread_ids": list(blocked_threads),
        "threads": threads_info,
        "main_thread": threading.main_thread().name,
    }


async def restart_application():
    """Background task to restart the application"""
    logger.info("Application restart initiated")
    time.sleep(2)  # Give time for response to be sent
    os._exit(0)  # Force restart (systemd/docker will restart the process)


@router.post("/restart", summary="Restart application")
async def restart(background_tasks: BackgroundTasks):
    """Restart the application (for development/testing purposes)"""
    logger.warning("Application restart requested")

    background_tasks.add_task(restart_application)

    return {
        "message": "Application restart initiated",
        "timestamp": datetime.now().isoformat(),
        "note": "The application will restart in 2 seconds",
    }
