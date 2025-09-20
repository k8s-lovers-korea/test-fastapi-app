"""
Thread simulation API endpoints.
"""

import asyncio
import logging
import threading
import time
from fastapi import APIRouter

from app.exceptions import ValidationError
from app.core.storage import blocking_lock, blocked_threads

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulate", tags=["⚡ Simulation (FastAPI Internal)"])


@router.post("/block", summary="Simulate blocking operation")
async def simulate_blocking():
    """⚡ **FastAPI Internal**: Start a blocking operation that will hold a lock for 30 seconds. Runs within the FastAPI application itself."""
    logger.info("Starting blocking simulation")

    def blocking_operation():
        thread_id = threading.current_thread().ident
        logger.info(f"Thread {thread_id} acquiring blocking lock")
        blocked_threads.add(thread_id)

        with blocking_lock:
            logger.info(f"Thread {thread_id} holding lock for 30 seconds")
            time.sleep(30)

        blocked_threads.discard(thread_id)
        logger.info(f"Thread {thread_id} released blocking lock")

    # Run blocking operation in background
    thread = threading.Thread(target=blocking_operation, name="BlockingSimulation")
    thread.daemon = True
    thread.start()

    return {
        "message": "Blocking operation started",
        "duration_seconds": 30,
        "thread_name": thread.name,
        "blocked_threads_count": len(blocked_threads),
    }


@router.get("/block/status", summary="Get blocking operation status")
async def get_blocking_status():
    """Get the current status of blocking operations"""
    logger.info("Getting blocking status")

    return {
        "blocked_threads_count": len(blocked_threads),
        "blocked_thread_ids": list(blocked_threads),
        "lock_available": not blocking_lock.locked(),
    }


@router.get("/timeout/{duration}", summary="Simulate timeout operation")
async def simulate_timeout(duration: int):
    """Simulate an operation that takes a specified time"""
    if duration < 1 or duration > 300:  # 5 minutes max
        raise ValidationError("Duration must be between 1 and 300 seconds")

    logger.info(f"Starting timeout simulation for {duration} seconds")

    start_time = time.time()
    await asyncio.sleep(duration)
    actual_duration = time.time() - start_time

    logger.info(f"Timeout simulation completed in {actual_duration:.2f} seconds")

    return {
        "message": "Operation completed after timeout",
        "requested_duration": duration,
        "actual_duration": round(actual_duration, 2),
        "completed_at": time.time(),
    }
