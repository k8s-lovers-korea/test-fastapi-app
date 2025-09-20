"""
Application configuration settings.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class"""

    # Application settings
    APP_NAME = os.getenv("APP_NAME", "Enhanced FastAPI Test Application")
    APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
    APP_DESCRIPTION = os.getenv(
        "APP_DESCRIPTION",
        "A comprehensive FastAPI app with CRUD, search, bulk operations, tracing, and metrics",
    )
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    RELOAD = os.getenv("RELOAD", "true").lower() == "true"

    # OpenTelemetry settings (for auto instrumentation)
    OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "test-fastapi-app")
    OTEL_SERVICE_VERSION = os.getenv("OTEL_SERVICE_VERSION", "2.0.0")
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    OTEL_EXPORTER_OTLP_HEADERS = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    HOSTNAME = os.getenv("HOSTNAME", "unknown")

    # Simulation settings
    MAX_TIMEOUT_DURATION = int(os.getenv("MAX_TIMEOUT_DURATION", "300"))
    DEFAULT_BLOCK_DURATION = int(os.getenv("DEFAULT_BLOCK_DURATION", "30"))

    # External Service - Spring Boot API
    SPRING_BOOT_API_BASE_URL = os.getenv(
        "SPRING_BOOT_API_BASE_URL", "http://localhost:8080"
    )

    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # OpenAPI configuration
    DOCS_URL = os.getenv("DOCS_URL", "/docs")
    REDOC_URL = os.getenv("REDOC_URL", "/redoc")
    OPENAPI_URL = os.getenv("OPENAPI_URL", "/openapi.json")

    @classmethod
    def get_openapi_description(cls) -> str:
        """Get detailed OpenAPI description"""
        return """
        A comprehensive FastAPI application demonstrating various architectural patterns:
        
        ## 🔗 External Service Integration
        * **TestEntity Operations**: Full CRUD operations that proxy to external Spring Boot API
        * **Test Scenarios**: Advanced load testing endpoints via external Spring Boot service
        * **Configuration Required**: Set `SPRING_BOOT_API_BASE_URL` environment variable
        
        ## 📦 FastAPI Internal Services
        * **Items**: Complete CRUD operations with in-memory storage
        * **Simulation**: Thread blocking and timeout scenarios within FastAPI
        * **Actuator**: Health checks, metrics, and system monitoring
        
        ## ✨ Key Features
        * **Bulk Operations**: Batch create and update operations
        * **Search & Filter**: Advanced search capabilities
        * **Observability**: Distributed tracing, metrics, and comprehensive logging
        * **Error Handling**: Comprehensive error handling for both internal and external services
        
        ## 🚀 Architecture Highlights
        Built with production-ready patterns including thread safety, circuit breaker patterns, 
        timeout handling, and seamless integration between internal FastAPI services and external APIs.
        
        **Note**: External API endpoints require proper Spring Boot service configuration and availability.
        """

    @classmethod
    def get_openapi_info(cls) -> Dict[str, Any]:
        """Get OpenAPI info configuration"""
        return {
            "x-logo": {
                "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
            }
        }

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "app_description": cls.APP_DESCRIPTION,
            "debug": cls.DEBUG,
            "host": cls.HOST,
            "port": cls.PORT,
            "reload": cls.RELOAD,
            "otel_service_name": cls.OTEL_SERVICE_NAME,
            "otel_service_version": cls.OTEL_SERVICE_VERSION,
            "otel_exporter_otlp_endpoint": cls.OTEL_EXPORTER_OTLP_ENDPOINT,
            "hostname": cls.HOSTNAME,
            "max_timeout_duration": cls.MAX_TIMEOUT_DURATION,
            "default_block_duration": cls.DEFAULT_BLOCK_DURATION,
            "spring_boot_api_base_url": cls.SPRING_BOOT_API_BASE_URL,
            "log_level": cls.LOG_LEVEL,
            "docs_url": cls.DOCS_URL,
            "redoc_url": cls.REDOC_URL,
            "openapi_url": cls.OPENAPI_URL,
        }
