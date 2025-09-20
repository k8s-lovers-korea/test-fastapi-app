"""
Test scenarios router for external Spring Boot API integration.
"""

from typing import Dict, Any
from fastapi import APIRouter, Query

from app.services import spring_boot_client

router = APIRouter(
    prefix="/api/test",
    tags=["🧪 Test Scenarios (External Spring Boot API)"],
    responses={
        503: {"description": "External service unavailable"},
        504: {"description": "External service timeout"},
    },
)


@router.get(
    "/health",
    summary="Basic health check",
    description="🧪 **External API Call**: Perform a basic health check against the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration.",
)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check via Spring Boot API.

    Returns the health status and basic information from the external service.
    """
    return await spring_boot_client.health_check()


@router.post(
    "/block-thread",
    summary="Block thread pool",
    description="🧪 **External API Call**: Exhaust request thread pool and block threads in the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration.",
)
async def block_thread(
    seconds: int = Query(
        default=30, description="Number of seconds to block threads", ge=1, le=300
    )
) -> Dict[str, Any]:
    """
    Exhaust request thread pool and block threads via Spring Boot API.

    - **seconds**: Duration in seconds to block threads (1-300, default: 30)

    This endpoint will cause the external service to block its thread pool,
    simulating high load conditions for testing purposes.
    """
    return await spring_boot_client.block_thread(seconds)


@router.post(
    "/hang",
    summary="Hang thread",
    description="🧪 **External API Call**: Hang a thread for a specified duration in the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration.",
)
async def hang_thread(
    seconds: int = Query(
        default=90, description="Number of seconds to hang thread", ge=1, le=300
    )
) -> Dict[str, Any]:
    """
    Hang thread for n seconds via Spring Boot API.

    - **seconds**: Duration in seconds to hang the thread (1-300, default: 90)

    This endpoint will cause the external service to hang a thread,
    simulating unresponsive behavior for testing purposes.
    """
    return await spring_boot_client.hang_thread(seconds)


@router.post(
    "/cpu-intensive",
    summary="CPU intensive task",
    description="🧪 **External API Call**: Execute a CPU intensive task in the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration.",
)
async def cpu_intensive_task(
    seconds: int = Query(
        default=10, description="Number of seconds for CPU intensive task", ge=1, le=300
    )
) -> Dict[str, Any]:
    """
    CPU intensive task via Spring Boot API.

    - **seconds**: Duration in seconds for the CPU intensive task (1-300, default: 10)

    This endpoint will cause the external service to perform CPU intensive operations,
    simulating high CPU load conditions for testing purposes.
    """
    return await spring_boot_client.cpu_intensive_task(seconds)


@router.get(
    "/thread-status",
    summary="Check thread status",
    description="🧪 **External API Call**: Check thread status and locks in the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration.",
)
async def get_thread_status() -> Dict[str, Any]:
    """
    Check thread status and locks via Spring Boot API.

    Returns detailed information about the current thread status,
    including active threads, locks, and other thread-related metrics
    from the external service.
    """
    return await spring_boot_client.get_thread_status()
