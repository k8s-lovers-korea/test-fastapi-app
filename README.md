# Enhanced FastAPI Test Application

A modern, production-ready FastAPI application demonstrating CRUD operations, OpenTelemetry auto-instrumentation, centralized configuration management, and comprehensive observability features.

## ✨ Key Features

- **🚀 Modern Architecture**: Clean separation of concerns with modular design
- **📊 CRUD Operations**: Full Create, Read, Update, Delete operations with in-memory storage
- **🔒 Thread Safety**: Thread-safe operations with RLock protection
- **🧵 Thread Simulation**: Blocking behavior and timeout scenarios for testing
- **📈 OpenTelemetry Auto-Instrumentation**: Automatic distributed tracing with OTLP support
- **⚙️ Centralized Configuration**: Environment-based config management with dotenv support
- **🔍 Observability**: Comprehensive logging and request tracing
- **🏥 Health Checks**: Production-ready actuator endpoints
- **📦 Modern Dependency Management**: Fast and reliable dependencies with uv

## 🏗️ Architecture

```
├── main.py                 # FastAPI application entry point
├── config.py              # Centralized configuration management
├── .env.example           # Environment variables template
├── app/
│   ├── core/
│   │   ├── observability.py  # OpenTelemetry setup
│   │   └── storage.py        # In-memory storage with thread safety
│   ├── routers/
│   │   ├── items.py          # CRUD operations
│   │   ├── actuator.py       # Health checks & monitoring
│   │   └── simulation.py     # Thread simulation endpoints
│   ├── models.py           # Pydantic data models
│   └── exceptions.py       # Custom exception handlers
```

## 🚀 Quick Start

### 1. Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and setup the project
```bash
git clone <repository-url>
cd test-fastapi-app
uv sync
```

### 3. Configure environment (optional)
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your preferred settings
# Most settings have sensible defaults
```

### 4. Run the application
```bash
# Development mode (with auto-reload)
uv run python main.py

# Or using uvicorn directly
uv run uvicorn main:app --reload
```

### 5. Access the application
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/actuator/health

## 📚 API Endpoints

### 🔧 CRUD Operations
- `POST /items/` - Create a new item
- `GET /items/` - Get all items with pagination
- `GET /items/{item_id}` - Get specific item
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item
- `GET /items/search` - Search items with filters
- `POST /items/bulk` - Create multiple items
- `PUT /items/bulk-update` - Update multiple items
- `DELETE /items/delete` - Delete multiple items

### 🧵 Simulation Endpoints
- `POST /simulate/block` - Simulate thread blocking (configurable duration)
- `GET /simulate/block/status` - Check blocking status
- `GET /simulate/timeout/{duration}` - Simulate timeout (supports >60s)

### 🏥 Actuator Endpoints
- `GET /actuator/health` - Comprehensive health check
- `GET /actuator/info` - Application information
- `GET /actuator/env` - Environment variables (filtered)
- `GET /actuator/threads` - Thread information
- `POST /actuator/restart` - Restart simulation

### 📊 Observability
- All endpoints automatically instrumented with OpenTelemetry
- Distributed tracing with span correlation
- Request/response logging with trace IDs

## 📦 Dependency Management

This project uses [uv](https://astral.sh/uv/) for lightning-fast dependency management:

**Key files:**
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Lockfile ensuring reproducible installs
- `.venv/` - Virtual environment (auto-created)

**Managing dependencies:**
```bash
# Add runtime dependency
uv add package-name

# Add development dependency  
uv add --dev package-name

# Remove dependency
uv remove package-name

# Update all dependencies
uv sync --upgrade
```

## ⚙️ Configuration

### Environment Variables Setup

The application uses a centralized configuration system with dotenv support:

1. **Copy the example file:**
```bash
cp .env.example .env
```

2. **Edit `.env` with your settings:**
```bash
# Application Configuration
APP_NAME=My Custom FastAPI App
APP_VERSION=1.0.0
DEBUG=false
HOST=0.0.0.0
PORT=8000

# OpenTelemetry Configuration
OTEL_SERVICE_NAME=my-fastapi-app
OTEL_SERVICE_VERSION=1.0.0
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer your-token

# Optional Settings
HOSTNAME=my-server
MAX_TIMEOUT_DURATION=300
DEFAULT_BLOCK_DURATION=30
```

### Available Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application display name | "Enhanced FastAPI Test Application" |
| `APP_VERSION` | Application version | "2.0.0" |
| `DEBUG` | Enable debug mode | false |
| `HOST` | Server bind address | "0.0.0.0" |
| `PORT` | Server port | 8000 |
| `RELOAD` | Auto-reload in development | true |
| `LOG_LEVEL` | Logging level | "INFO" |
| **OpenTelemetry** | | |
| `OTEL_SERVICE_NAME` | Service name for tracing | "test-fastapi-app" |
| `OTEL_SERVICE_VERSION` | Service version | "2.0.0" |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP endpoint URL | None (disabled) |
| `OTEL_EXPORTER_OTLP_HEADERS` | OTLP auth headers | None |
| `HOSTNAME` | Service instance ID | "unknown" |
| **Simulation** | | |
| `MAX_TIMEOUT_DURATION` | Max timeout seconds | 300 |
| `DEFAULT_BLOCK_DURATION` | Default block duration | 30 |

### 🔍 OpenTelemetry Auto-Instrumentation

The application features **zero-configuration** OpenTelemetry instrumentation:

- ✅ **FastAPI**: All HTTP requests and responses
- ✅ **Requests**: Outbound HTTP calls  
- ✅ **Custom Spans**: Business logic tracing
- ✅ **Correlation**: Trace IDs in logs

### 🎯 Quick Observability Setup

**With Jaeger (Docker):**
```bash
# 1. Start Jaeger
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# 2. Configure your .env
echo "OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317" >> .env

# 3. Run the app
uv run python main.py

# 4. View traces at http://localhost:16686
```

**With Custom OTLP Collector:**
```bash
# Configure for your observability platform
export OTEL_SERVICE_NAME="my-production-app"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://your-otlp-endpoint:4317"
export OTEL_EXPORTER_OTLP_HEADERS="authorization=Bearer your-api-key"

uv run python main.py
```

## 💡 Example Usage

### Basic CRUD Operations
```bash
# Create an item
curl -X POST "http://localhost:8000/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptop", 
    "description": "High-performance gaming laptop", 
    "price": 1299.99, 
    "in_stock": true,
    "tags": ["gaming", "laptop", "electronics"]
  }'

# Get all items with pagination
curl "http://localhost:8000/items/?skip=0&limit=10"

# Search items
curl "http://localhost:8000/items/search?query=laptop&min_price=1000"

# Update an item
curl -X PUT "http://localhost:8000/items/{item_id}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Laptop", "price": 1199.99}'
```

### Simulation Endpoints
```bash
# Simulate 90-second timeout
curl "http://localhost:8000/simulate/timeout/90"

# Trigger thread blocking simulation
curl -X POST "http://localhost:8000/simulate/block"

# Check blocking status
curl "http://localhost:8000/simulate/block/status"
```

### Health & Monitoring
```bash
# Comprehensive health check
curl "http://localhost:8000/actuator/health" | jq

# Application info
curl "http://localhost:8000/actuator/info" | jq

# Thread information
curl "http://localhost:8000/actuator/threads" | jq
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.