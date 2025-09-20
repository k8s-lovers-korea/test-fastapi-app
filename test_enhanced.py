import pytest
import time
from fastapi.testclient import TestClient
from main import app, items_storage, storage_lock

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test"""
    with storage_lock:
        items_storage.clear()

def test_enhanced_root_endpoint():
    """Test the enhanced root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Enhanced FastAPI Test Application"
    assert data["version"] == "2.0.0"
    assert "uptime_seconds" in data
    assert "features" in data
    assert "endpoints" in data
    assert "statistics" in data

def test_bulk_create_items():
    """Test bulk item creation"""
    items_data = {
        "items": [
            {"name": "Item 1", "description": "First item", "price": 10.0, "tags": ["tag1"]},
            {"name": "Item 2", "description": "Second item", "price": 20.0, "tags": ["tag2"]},
            {"name": "Item 3", "description": "Third item", "price": 30.0, "tags": ["tag1", "tag2"]}
        ]
    }
    
    response = client.post("/items/bulk", json=items_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    for i, item in enumerate(data):
        assert item["name"] == f"Item {i+1}"
        assert "id" in item
        assert "created_at" in item
        assert "updated_at" in item

def test_search_items():
    """Test item search functionality"""
    # First create some test items
    items_data = {
        "items": [
            {"name": "Gaming Laptop", "description": "High-end gaming", "price": 1500.0, "tags": ["gaming", "electronics"]},
            {"name": "Office Laptop", "description": "Business laptop", "price": 800.0, "tags": ["office", "electronics"]},
            {"name": "Gaming Mouse", "description": "RGB gaming mouse", "price": 50.0, "tags": ["gaming", "accessories"]}
        ]
    }
    
    create_response = client.post("/items/bulk", json=items_data)
    assert create_response.status_code == 200
    
    # Test text search
    search_data = {"query": "gaming"}
    response = client.post("/items/search", json=search_data)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2  # Gaming Laptop and Gaming Mouse
    
    # Test price range search
    search_data = {"min_price": 100.0, "max_price": 1000.0}
    response = client.post("/items/search", json=search_data)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1  # Only Office Laptop
    
    # Test tag search
    search_data = {"tags": ["office"]}
    response = client.post("/items/search", json=search_data)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1  # Only Office Laptop

def test_bulk_update_items():
    """Test bulk item updates"""
    # Create items first
    items_data = {
        "items": [
            {"name": "Item 1", "price": 10.0},
            {"name": "Item 2", "price": 20.0}
        ]
    }
    
    create_response = client.post("/items/bulk", json=items_data)
    created_items = create_response.json()
    
    # Bulk update
    updates = {
        "updates": {
            created_items[0]["id"]: {"price": 15.0, "name": "Updated Item 1"},
            created_items[1]["id"]: {"price": 25.0}
        }
    }
    
    response = client.put("/items/bulk-update", json=updates)
    assert response.status_code == 200
    updated_items = response.json()
    
    assert len(updated_items) == 2
    assert updated_items[created_items[0]["id"]]["price"] == 15.0
    assert updated_items[created_items[0]["id"]]["name"] == "Updated Item 1"
    assert updated_items[created_items[1]["id"]]["price"] == 25.0

def test_bulk_delete_items():
    """Test bulk item deletion"""
    # Create items first
    items_data = {
        "items": [
            {"name": "Item 1", "price": 10.0},
            {"name": "Item 2", "price": 20.0},
            {"name": "Item 3", "price": 30.0}
        ]
    }
    
    create_response = client.post("/items/bulk", json=items_data)
    created_items = create_response.json()
    
    # Delete first two items
    item_ids = [created_items[0]["id"], created_items[1]["id"], "nonexistent-id"]
    
    response = client.post("/items/delete", json=item_ids)
    assert response.status_code == 200
    data = response.json()
    
    assert data["deleted_count"] == 2
    assert data["not_found_count"] == 1
    assert "nonexistent-id" in data["not_found_ids"]
    
    # Verify items are deleted
    response = client.get("/items/")
    remaining_items = response.json()
    assert len(remaining_items) == 1
    assert remaining_items[0]["id"] == created_items[2]["id"]

def test_enhanced_health_check():
    """Test enhanced health check endpoint"""
    response = client.get("/actuator/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "UP"
    assert "timestamp" in data
    assert "details" in data
    assert "system_info" in data
    
    # Check system info fields
    system_info = data["system_info"]
    assert "python_version" in system_info
    assert "platform" in system_info
    assert "memory_total_mb" in system_info

def test_actuator_env_endpoint():
    """Test environment information endpoint"""
    response = client.get("/actuator/env")
    assert response.status_code == 200
    data = response.json()
    
    assert "environment" in data
    assert "configuration" in data
    assert "runtime" in data
    
    assert "python_version" in data["environment"]
    assert "process_id" in data["runtime"]

def test_actuator_threads_endpoint():
    """Test thread information endpoint"""
    response = client.get("/actuator/threads")
    assert response.status_code == 200
    data = response.json()
    
    assert "active_count" in data
    assert "blocked_count" in data
    assert "main_thread" in data
    assert "threads" in data
    assert "locks" in data
    
    assert isinstance(data["threads"], list)
    assert len(data["threads"]) > 0

def test_enhanced_metrics():
    """Test enhanced custom metrics"""
    # Create some items first to have data
    item_data = {"name": "Test Item", "price": 10.0}
    client.post("/items/", json=item_data)
    
    response = client.get("/actuator/metrics")
    assert response.status_code == 200
    data = response.json()
    
    assert "application" in data
    assert "items" in data
    assert "threading" in data
    assert "system" in data
    
    # Check application metrics
    assert "uptime_seconds" in data["application"]
    assert "startup_time" in data["application"]
    
    # Check items metrics
    assert data["items"]["total_count"] >= 1
    assert "created_total" in data["items"]
    
    # Check threading metrics
    assert "active_threads_count" in data["threading"]

def test_pagination():
    """Test item pagination"""
    # Create multiple items
    items_data = {
        "items": [{"name": f"Item {i}", "price": float(i)} for i in range(1, 11)]
    }
    
    client.post("/items/bulk", json=items_data)
    
    # Test pagination
    response = client.get("/items/?limit=5&offset=0")
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1) == 5
    
    response = client.get("/items/?limit=5&offset=5")
    assert response.status_code == 200
    page2 = response.json()
    assert len(page2) == 5
    
    # Ensure different items
    page1_ids = {item["id"] for item in page1}
    page2_ids = {item["id"] for item in page2}
    assert page1_ids.isdisjoint(page2_ids)

def test_enhanced_timeout_simulation():
    """Test enhanced timeout simulation"""
    start_time = time.time()
    response = client.get("/simulate/timeout/3")
    end_time = time.time()
    
    assert response.status_code == 200
    data = response.json()
    assert data["requested_duration"] == 3
    assert data["actual_duration"] >= 3
    assert "start_time" in data
    assert "end_time" in data
    assert end_time - start_time >= 3

def test_enhanced_blocking_status():
    """Test enhanced blocking status"""
    response = client.get("/simulate/block/status")
    assert response.status_code == 200
    data = response.json()
    
    assert "blocked_threads" in data
    assert "blocked_count" in data
    assert "lock_available" in data
    assert "active_threads" in data

def test_validation_errors():
    """Test custom validation errors"""
    # Test invalid item creation
    invalid_item = {"name": "", "price": -10.0}  # Empty name, negative price
    response = client.post("/items/", json=invalid_item)
    assert response.status_code == 422  # Validation error
    
    # Test invalid timeout duration
    response = client.get("/simulate/timeout/400")  # Exceeds 300s limit
    assert response.status_code == 400
    assert "Maximum timeout duration" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__])