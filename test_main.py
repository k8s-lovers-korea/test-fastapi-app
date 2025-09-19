import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from main import app, items_storage, storage_lock

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test"""
    with storage_lock:
        items_storage.clear()

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/actuator/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert "timestamp" in data
    assert "details" in data

def test_create_item():
    """Test creating a new item"""
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 29.99,
        "in_stock": True
    }
    response = client.post("/items/", json=item_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == item_data["name"]
    assert data["price"] == item_data["price"]
    assert "id" in data

def test_get_items():
    """Test getting all items"""
    # First create an item
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 29.99,
        "in_stock": True
    }
    create_response = client.post("/items/", json=item_data)
    assert create_response.status_code == 200
    
    # Then get all items
    response = client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == item_data["name"]

def test_get_item_by_id():
    """Test getting a specific item by ID"""
    # Create an item first
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 29.99,
        "in_stock": True
    }
    create_response = client.post("/items/", json=item_data)
    created_item = create_response.json()
    item_id = created_item["id"]
    
    # Get the item by ID
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["name"] == item_data["name"]

def test_get_nonexistent_item():
    """Test getting a non-existent item"""
    response = client.get("/items/nonexistent-id")
    assert response.status_code == 404
    assert "Item not found" in response.json()["detail"]

def test_update_item():
    """Test updating an item"""
    # Create an item first
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 29.99,
        "in_stock": True
    }
    create_response = client.post("/items/", json=item_data)
    created_item = create_response.json()
    item_id = created_item["id"]
    
    # Update the item
    update_data = {
        "name": "Updated Item",
        "price": 39.99
    }
    response = client.put(f"/items/{item_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["price"] == update_data["price"]
    assert data["description"] == item_data["description"]  # Should remain unchanged

def test_delete_item():
    """Test deleting an item"""
    # Create an item first
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 29.99,
        "in_stock": True
    }
    create_response = client.post("/items/", json=item_data)
    created_item = create_response.json()
    item_id = created_item["id"]
    
    # Delete the item
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify item is deleted
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 404

def test_simulate_blocking():
    """Test thread blocking simulation"""
    response = client.post("/simulate/block")
    assert response.status_code == 200
    data = response.json()
    assert "Thread blocking simulation started" in data["message"]
    assert data["duration"] == "30 seconds"

def test_blocking_status():
    """Test getting blocking status"""
    response = client.get("/simulate/block/status")
    assert response.status_code == 200
    data = response.json()
    assert "blocked_threads" in data
    assert "lock_available" in data

def test_simulate_timeout_short():
    """Test timeout simulation with short duration"""
    start_time = time.time()
    response = client.get("/simulate/timeout/2")
    end_time = time.time()
    
    assert response.status_code == 200
    data = response.json()
    assert data["requested_duration"] == 2
    assert data["actual_duration"] >= 2
    assert end_time - start_time >= 2

def test_simulate_timeout_invalid():
    """Test timeout simulation with invalid duration"""
    response = client.get("/simulate/timeout/400")
    assert response.status_code == 400
    assert "Maximum timeout duration" in response.json()["detail"]

def test_app_info():
    """Test application info endpoint"""
    response = client.get("/actuator/info")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["app"]["name"] == "test-fastapi-app"
    assert data["app"]["version"] == "1.0.0"

def test_trigger_restart():
    """Test restart trigger endpoint"""
    response = client.post("/actuator/restart")
    assert response.status_code == 200
    data = response.json()
    assert "Application restart initiated" in data["message"]
    assert "timestamp" in data

def test_custom_metrics():
    """Test custom metrics endpoint"""
    response = client.get("/actuator/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "items_total" in data
    assert "blocked_threads_count" in data
    assert "lock_status" in data
    assert "timestamp" in data

if __name__ == "__main__":
    pytest.main([__file__])