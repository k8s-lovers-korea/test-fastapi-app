"""
OpenTelemetry observability configuration for distributed tracing and monitoring.
"""

import logging
from fastapi import FastAPI

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Import Config (avoid circular import by importing here)
from .config import Config

logger = logging.getLogger(__name__)


def setup_telemetry():
    """Setup OpenTelemetry tracing"""

    # Set up resource with service information
    resource = Resource.create(
        {
            "service.name": Config.OTEL_SERVICE_NAME,
            "service.version": Config.OTEL_SERVICE_VERSION,
            "service.instance.id": Config.HOSTNAME,
        }
    )

    # Set up tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Configure OTLP exporter (can be disabled if OTEL_EXPORTER_OTLP_ENDPOINT is not set)
    otlp_endpoint = Config.OTEL_EXPORTER_OTLP_ENDPOINT
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=(
                {"Authorization": f"Bearer {Config.OTEL_EXPORTER_OTLP_HEADERS}"}
                if Config.OTEL_EXPORTER_OTLP_HEADERS
                else None
            ),
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        logger.info(
            f"OpenTelemetry OTLP exporter configured with endpoint: {otlp_endpoint}"
        )
    else:
        logger.info(
            "OpenTelemetry OTLP exporter not configured (OTEL_EXPORTER_OTLP_ENDPOINT not set)"
        )

    # Auto-instrument libraries
    RequestsInstrumentor().instrument()
    logger.info("OpenTelemetry auto-instrumentation setup completed")


def instrument_fastapi_app(app: FastAPI):
    """Instrument FastAPI app with OpenTelemetry"""
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI app instrumented with OpenTelemetry")
