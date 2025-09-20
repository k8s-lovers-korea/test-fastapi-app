"""
Custom exception classes for the FastAPI application.
"""
from fastapi import HTTPException


class ItemNotFoundError(HTTPException):
    def __init__(self, item_id: str):
        super().__init__(status_code=404, detail=f"Item with id {item_id} not found")


class ValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=400, detail=message)