# FastAPI Test Application

A comprehensive FastAPI application demonstrating CRUD operations, distributed tracing, metrics collection, and thread simulation capabilities.

## Features

- **CRUD Operations**: Full Create, Read, Update, Delete operations for items stored in memory
- **Thread Safety**: Thread-safe operations with RLock protection
- **Thread Blocking Simulation**: Simulate thread lock behavior and blocking scenarios
- **Timeout Simulation**: Configurable timeout scenarios (supports >60 seconds)
- **Distributed Tracing**: OpenTelemetry integration with OTLP and Jaeger exporters
- **Metrics Collection**: Prometheus metrics via prometheus_fastapi_instrumentator
- **Request Logging**: Comprehensive logging of all incoming requests and internal events
- **Actuator Endpoints**: Health checks, info, restart simulation, and custom metrics
- **Docker Support**: Complete containerization with docker-compose for observability stack

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python run.py
# or
uvicorn main:app --reload
```

3. Access the application at `http://localhost:8000`

### Docker Compose (Recommended)

Run the complete observability stack:

```bash
docker-compose up -d
```

This starts:
- FastAPI app at `http://localhost:8000`
- Jaeger UI at `http://localhost:16686`
- Prometheus at `http://localhost:9090`
- Grafana at `http://localhost:3000` (admin/admin)

## API Endpoints

### CRUD Operations
- `POST /items/` - Create a new item
- `GET /items/` - Get all items
- `GET /items/{item_id}` - Get specific item
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item

### Simulation Endpoints
- `POST /simulate/block` - Simulate thread blocking (30s duration)
- `GET /simulate/block/status` - Check blocking status
- `GET /simulate/timeout/{duration}` - Simulate timeout (supports >60s)

### Actuator Endpoints
- `GET /actuator/health` - Health check
- `GET /actuator/info` - Application info
- `POST /actuator/restart` - Trigger restart simulation
- `GET /actuator/metrics` - Custom metrics

### Observability
- `GET /metrics` - Prometheus metrics
- Distributed tracing automatically enabled for all endpoints

## Configuration

Environment variables:
- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `OTLP_ENDPOINT`: OTLP exporter endpoint (default: http://localhost:4317)
- `JAEGER_HOST`: Jaeger host (default: localhost)
- `JAEGER_PORT`: Jaeger port (default: 6831)

## Testing

Run tests:
```bash
pytest test_main.py -v
```

## Example Usage

### Create an item:
```bash
curl -X POST "http://localhost:8000/items/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "description": "Gaming laptop", "price": 1299.99, "in_stock": true}'
```

### Simulate 90-second timeout:
```bash
curl "http://localhost:8000/simulate/timeout/90"
```

### Trigger thread blocking:
```bash
curl -X POST "http://localhost:8000/simulate/block"
```

### Check health:
```bash
curl "http://localhost:8000/actuator/health"
```

## Architecture

The application demonstrates:
- **Thread-safe in-memory storage** with Python's RLock
- **OpenTelemetry tracing** with automatic span creation
- **Prometheus metrics** collection and exposure
- **Structured logging** for all operations
- **Background task processing** for simulations
- **Comprehensive error handling** with proper HTTP status codes

## Observability Features

- **Request tracing**: Every request gets a unique trace span
- **Performance metrics**: Response times, request counts, error rates
- **Custom business metrics**: Item counts, thread status, lock availability
- **Health monitoring**: Application status and component health
- **Log correlation**: Trace IDs in logs for easy debugging