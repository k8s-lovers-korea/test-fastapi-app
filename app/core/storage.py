"""
In-memory storage, locks, and search functionality.
"""

import threading
from typing import Dict, List
from datetime import datetime
from app.models import Item, ItemSearch


# In-memory storage with thread safety
items_storage: Dict[str, Item] = {}
storage_lock = threading.RLock()
blocking_lock = threading.Lock()

# Global state for simulating blocking
is_blocked = False
blocked_threads = set()

# Application startup time
startup_time = datetime.now()


def search_items(search_params: ItemSearch) -> List[Item]:
    """Search items based on criteria"""
    results = []

    with storage_lock:
        for item in items_storage.values():
            # Text search in name and description
            if search_params.query:
                query_lower = search_params.query.lower()
                if query_lower not in item.name.lower() and (
                    not item.description or query_lower not in item.description.lower()
                ):
                    continue

            # Price range filter
            if (
                search_params.min_price is not None
                and item.price < search_params.min_price
            ):
                continue
            if (
                search_params.max_price is not None
                and item.price > search_params.max_price
            ):
                continue

            # Stock status filter
            if (
                search_params.in_stock is not None
                and item.in_stock != search_params.in_stock
            ):
                continue

            # Tags filter
            if search_params.tags:
                if not item.tags or not any(
                    tag in item.tags for tag in search_params.tags
                ):
                    continue

            results.append(item)

    return results


def get_storage_stats():
    """Get storage statistics"""
    # Try to acquire the lock without blocking to check availability
    storage_available = storage_lock.acquire(blocking=False)
    if storage_available:
        storage_lock.release()

    return {
        "items_count": len(items_storage),
        "blocked_threads_count": len(blocked_threads),
        "storage_lock_available": storage_available,
        "blocking_lock_available": not blocking_lock.locked(),
    }
