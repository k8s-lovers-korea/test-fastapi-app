import os
from typing import Dict, Any

# Configuration settings
class Config:
    # Application settings
    APP_NAME = os.getenv("APP_NAME", "test-fastapi-app")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # OpenTelemetry settings
    OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
    JAEGER_HOST = os.getenv("JAEGER_HOST", "localhost")
    JAEGER_PORT = int(os.getenv("JAEGER_PORT", "6831"))
    
    # Simulation settings
    MAX_TIMEOUT_DURATION = int(os.getenv("MAX_TIMEOUT_DURATION", "300"))
    DEFAULT_BLOCK_DURATION = int(os.getenv("DEFAULT_BLOCK_DURATION", "30"))
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "debug": cls.DEBUG,
            "host": cls.HOST,
            "port": cls.PORT,
            "otlp_endpoint": cls.OTLP_ENDPOINT,
            "jaeger_host": cls.JAEGER_HOST,
            "jaeger_port": cls.JAEGER_PORT,
            "max_timeout_duration": cls.MAX_TIMEOUT_DURATION,
            "default_block_duration": cls.DEFAULT_BLOCK_DURATION,
        }