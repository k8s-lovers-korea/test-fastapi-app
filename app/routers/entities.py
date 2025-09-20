"""
TestEntity CRUD router for extern@router.get(
    "/{@router.post(
    "",
 @router.put(
    "/{en@router.delete(
   @router.get(
    "/search",
    response_model=List[TestEntity],
    summary="Search entities by name",
    description="🔗 **External API Call**: Search for TestEntity records by name in the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration."
)tity_id}",
    summary="Delete entity",
    description="🔗 **External API Call**: Delete a TestEntity from the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration."
)id}",
    response_model=TestEntity,
    summary="Update entity",
    description="🔗 **External API Call**: Update an existing TestEntity in the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration."
)ponse_model=TestEntity,
    status_code=201,
    summary="Create new entity",
    description="🔗 **External API Call**: Create a new TestEntity in the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration."
)id}",
    response_model=TestEntity,
    summary="Get entity by ID",
    description="🔗 **External API Call**: Retrieve a specific TestEntity by its unique identifier from the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration."
)ing Boot API integration.
"""

from typing import List
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.models import TestEntity, TestEntityCreate, TestEntityUpdate
from app.services import spring_boot_client

router = APIRouter(
    prefix="/api/entities",
    tags=["🔗 TestEntity Operations (External Spring Boot API)"],
    responses={
        404: {"description": "Entity not found"},
        503: {"description": "External service unavailable"},
        504: {"description": "External service timeout"},
    },
)


@router.get(
    "",
    response_model=List[TestEntity],
    summary="Get all entities",
    description="🔗 **External API Call**: Retrieve all TestEntity records from the external Spring Boot service. Requires SPRING_BOOT_API_BASE_URL configuration.",
)
async def get_all_entities():
    """
    Get all entities from Spring Boot API.

    Returns a list of all TestEntity objects available in the external service.
    """
    return await spring_boot_client.get_all_entities()


@router.get(
    "/{entity_id}",
    response_model=TestEntity,
    summary="Get entity by ID",
    description="Retrieve a specific TestEntity by its unique identifier from the external Spring Boot service.",
)
async def get_entity_by_id(entity_id: int):
    """
    Get entity by ID from Spring Boot API.

    - **entity_id**: The unique identifier of the entity to retrieve
    """
    return await spring_boot_client.get_entity_by_id(entity_id)


@router.post(
    "",
    response_model=TestEntity,
    status_code=201,
    summary="Create new entity",
    description="Create a new TestEntity in the external Spring Boot service.",
)
async def create_entity(entity: TestEntityCreate):
    """
    Create new entity via Spring Boot API.

    - **name**: The name of the entity (required, 1-100 characters)
    - **description**: Optional description of the entity (max 500 characters)
    """
    return await spring_boot_client.create_entity(entity)


@router.put(
    "/{entity_id}",
    response_model=TestEntity,
    summary="Update entity",
    description="Update an existing TestEntity in the external Spring Boot service.",
)
async def update_entity(entity_id: int, entity: TestEntityUpdate):
    """
    Update entity via Spring Boot API.

    - **entity_id**: The unique identifier of the entity to update
    - **name**: Optional new name for the entity (1-100 characters)
    - **description**: Optional new description for the entity (max 500 characters)
    """
    return await spring_boot_client.update_entity(entity_id, entity)


@router.delete(
    "/{entity_id}",
    summary="Delete entity",
    description="Delete a TestEntity from the external Spring Boot service.",
)
async def delete_entity(entity_id: int):
    """
    Delete entity via Spring Boot API.

    - **entity_id**: The unique identifier of the entity to delete
    """
    result = await spring_boot_client.delete_entity(entity_id)
    return JSONResponse(content=result, status_code=200)


@router.get(
    "/search",
    response_model=List[TestEntity],
    summary="Search entities by name",
    description="Search for TestEntity records by name in the external Spring Boot service.",
)
async def search_entities_by_name(
    name: str = Query(..., description="Name to search for")
):
    """
    Search entities by name via Spring Boot API.

    - **name**: The name pattern to search for in entity names
    """
    return await spring_boot_client.search_entities_by_name(name)
