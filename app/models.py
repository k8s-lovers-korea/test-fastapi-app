"""
Pydantic models for the FastAPI application.
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class Item(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(
        None, max_length=500, description="Item description"
    )
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    in_stock: bool = Field(True, description="Whether item is in stock")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: Optional[List[str]] = Field(
        default_factory=list, description="Item tags for categorization"
    )


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    in_stock: Optional[bool] = None
    tags: Optional[List[str]] = None


class ItemSearch(BaseModel):
    query: Optional[str] = Field(
        None, description="Search query for name or description"
    )
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None
    tags: Optional[List[str]] = None


class BulkItemCreate(BaseModel):
    items: List[Item] = Field(..., min_length=1, max_length=100)


class ItemUpdateWithId(ItemUpdate):
    id: str = Field(..., description="Item ID to update")


class BulkItemUpdate(BaseModel):
    updates: List[ItemUpdateWithId] = Field(..., min_length=1, max_length=100)


# TestEntity models for Spring Boot API integration
class TestEntity(BaseModel):
    """TestEntity model for external Spring Boot API"""

    id: Optional[int] = Field(None, description="Entity ID")
    name: str = Field(..., min_length=1, max_length=100, description="Entity name")
    description: Optional[str] = Field(
        None, max_length=500, description="Entity description"
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TestEntityCreate(BaseModel):
    """Model for creating TestEntity"""

    name: str = Field(..., min_length=1, max_length=100, description="Entity name")
    description: Optional[str] = Field(
        None, max_length=500, description="Entity description"
    )


class TestEntityUpdate(BaseModel):
    """Model for updating TestEntity"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Entity name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Entity description"
    )


class TestScenarioResponse(BaseModel):
    """Response model for test scenarios"""

    message: str
    duration: Optional[float] = None
    thread_info: Optional[Dict[str, Union[str, int]]] = None
