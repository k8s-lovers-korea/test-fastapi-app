# FastAPI Test Application for AI-SRE Agent

A test FastAPI application designed for AI-SRE agent development.
Provides various testing scenarios and Spring Boot application integration capabilities.

## Key Features

- **CRUD API**: Basic data create/read/update/delete operations
- **Spring Boot Integration**: Communication with external Spring Boot applications
- **Simulation Endpoints**: Various test scenarios including blocking and timeout behaviors
- **Health Checks**: Application status monitoring
- **OpenTelemetry**: Distributed tracing and observability

## Quick Start

### 1. Install and run
```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py
```

### 2. Access the application
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/actuator/health

## API Endpoints

### Key Endpoints for AI-SRE Testing
- `GET /api/entities` - Get entities (calls Spring Boot app)
- `POST /simulate/block` - Simulate blocking behavior
- `GET /simulate/timeout/{duration}` - Simulate timeout scenarios
- `GET /actuator/health` - Health check endpoint
- `POST /items/` - Create test data
- `GET /items/` - Retrieve test data

## Example Usage

```bash
# Test Spring Boot integration
curl "http://localhost:8000/api/entities"

# Test simulation scenarios
curl -X POST "http://localhost:8000/simulate/block"
curl "http://localhost:8000/simulate/timeout/30"

# Health check
curl "http://localhost:8000/actuator/health"
```

## Purpose

This application serves as a test target for AI-SRE agent development, providing:
- Integration patterns with Spring Boot services
- Various failure scenarios for testing resilience
- Observability features for monitoring and tracing

## FluxCD OCI Deployment

This application supports FluxCD deployment with OCI artifacts:

- **CI/CD**: GitHub Actions builds and pushes container images and Kubernetes manifests as OCI artifacts
- **FluxCD**: Automatically deploys to `sample-apps` namespace with health monitoring
- **Structure**: `.github/workflows/`, `k8s/`, and `flux/` directories contain all deployment configurations

### Quick Deploy
```bash
kubectl apply -f flux/oci-repository.yaml
kubectl apply -f flux/kustomization.yaml
```