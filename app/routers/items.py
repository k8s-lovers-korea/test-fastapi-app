"""
Items CRUD API endpoints.
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Query

from app.models import Item, ItemUpdate, ItemSearch, BulkItemCreate, BulkItemUpdate
from app.exceptions import ItemNotFoundError
from app.core.storage import items_storage, storage_lock, search_items

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items", tags=["📦 Items (FastAPI Internal)"])


@router.post("/", response_model=Item, summary="Create a new item")
async def create_item(item: Item):
    """📦 **FastAPI Internal**: Create a new item with automatic ID generation and validation. Data is stored in FastAPI application memory."""
    logger.info(f"Creating item: {item.name}")

    with storage_lock:
        # Generate new ID
        new_id = str(uuid.uuid4())

        # Create item with server-assigned properties
        new_item = Item(
            id=new_id,
            name=item.name,
            description=item.description,
            price=item.price,
            in_stock=item.in_stock,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=item.tags or [],
        )

        items_storage[new_id] = new_item
        logger.info(f"Item created successfully: {new_id}")

        return new_item


@router.post("/bulk", response_model=List[Item], summary="Create multiple items")
async def create_items_bulk(bulk_request: BulkItemCreate):
    """Create multiple items in a single request"""
    logger.info(f"Creating {len(bulk_request.items)} items in bulk")

    created_items = []

    with storage_lock:
        for item_data in bulk_request.items:
            new_id = str(uuid.uuid4())
            new_item = Item(
                id=new_id,
                name=item_data.name,
                description=item_data.description,
                price=item_data.price,
                in_stock=item_data.in_stock,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=item_data.tags or [],
            )
            items_storage[new_id] = new_item
            created_items.append(new_item)

        logger.info(f"Successfully created {len(created_items)} items")

        return created_items


@router.get("/", response_model=List[Item], summary="Get all items")
async def get_all_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
):
    """Get all items with pagination support"""
    logger.info(f"Getting items with skip={skip}, limit={limit}")

    with storage_lock:
        all_items = list(items_storage.values())

        # Apply pagination
        paginated_items = all_items[skip : skip + limit]

        logger.info(f"Retrieved {len(paginated_items)} items")
        return paginated_items


@router.get("/search", response_model=List[Item], summary="Search items")
async def search_items_endpoint(
    query: Optional[str] = Query(
        None, description="Search query for name or description"
    ),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
):
    """Search items based on various criteria using query parameters"""
    # Create ItemSearch object from query parameters
    search = ItemSearch(
        query=query,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        tags=tags,
    )

    logger.info(f"Searching items with criteria: {search}")

    with storage_lock:
        results = search_items(search)
        logger.info(f"Search returned {len(results)} items")
        return results


@router.get("/{item_id}", response_model=Item, summary="Get a specific item")
async def get_item(item_id: str):
    """Get a specific item by ID"""
    logger.info(f"Getting item: {item_id}")

    with storage_lock:
        if item_id not in items_storage:
            logger.warning(f"Item not found: {item_id}")
            raise ItemNotFoundError(item_id)

        item = items_storage[item_id]
        logger.info(f"Retrieved item: {item_id}")
        return item


@router.put("/{item_id}", response_model=Item, summary="Update an item")
async def update_item(item_id: str, update_data: ItemUpdate):
    """Update an existing item"""
    logger.info(f"Updating item: {item_id}")

    with storage_lock:
        if item_id not in items_storage:
            logger.warning(f"Item not found for update: {item_id}")
            raise ItemNotFoundError(item_id)

        existing_item = items_storage[item_id]

        # Apply updates only for provided fields
        update_dict = update_data.dict(exclude_unset=True)

        if update_dict:
            for field, value in update_dict.items():
                setattr(existing_item, field, value)

            # Always update the timestamp
            existing_item.updated_at = datetime.now()

            logger.info(f"Item updated successfully: {item_id}")

        return existing_item


@router.put("/bulk-update", response_model=List[Item], summary="Update multiple items")
async def update_items_bulk(bulk_request: BulkItemUpdate):
    """Update multiple items in a single request"""
    logger.info(f"Bulk updating {len(bulk_request.updates)} items")

    updated_items = []
    not_found_ids = []

    with storage_lock:
        for update_item in bulk_request.updates:
            item_id = update_item.id

            if item_id in items_storage:
                existing_item = items_storage[item_id]
                update_dict = update_item.dict(exclude_unset=True, exclude={"id"})

                if update_dict:
                    for field, value in update_dict.items():
                        setattr(existing_item, field, value)
                    existing_item.updated_at = datetime.now()

                updated_items.append(existing_item)
            else:
                not_found_ids.append(item_id)

        logger.info(
            f"Updated {len(updated_items)} items, {len(not_found_ids)} not found"
        )

        return updated_items


@router.delete("/{item_id}", summary="Delete an item")
async def delete_item(item_id: str):
    """Delete a specific item"""
    logger.info(f"Deleting item: {item_id}")

    with storage_lock:
        if item_id not in items_storage:
            logger.warning(f"Item not found for deletion: {item_id}")
            raise ItemNotFoundError(item_id)

        deleted_item = items_storage.pop(item_id)
        logger.info(f"Item deleted successfully: {item_id}")

        return {"message": f"Item {item_id} deleted successfully", "item": deleted_item}


@router.delete("/bulk", summary="Delete multiple items")
async def delete_items_bulk(
    item_ids: List[str] = Query(..., description="List of item IDs to delete")
):
    """Delete multiple items by their IDs via query parameters"""
    logger.info(f"Bulk deleting {len(item_ids)} items")

    deleted_items = {}
    not_found_ids = []

    with storage_lock:
        for item_id in item_ids:
            if item_id in items_storage:
                deleted_items[item_id] = items_storage.pop(item_id)
            else:
                not_found_ids.append(item_id)

        logger.info(
            f"Deleted {len(deleted_items)} items, {len(not_found_ids)} not found"
        )

        return {
            "message": "Bulk delete completed",
            "deleted_count": len(deleted_items),
            "not_found_count": len(not_found_ids),
            "deleted_items": deleted_items,
            "not_found_ids": not_found_ids,
        }
