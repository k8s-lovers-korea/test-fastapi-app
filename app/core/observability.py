"""
OpenTelemetry observability configuration for distributed tracing and monitoring.
"""

import logging
from fastapi import FastAPI

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor

# Import Config (avoid circular import by importing here)
from .config import Config

logger = logging.getLogger(__name__)

# Global meter instance for custom metrics
_meter = None


def get_meter():
    """Get the global meter instance for creating custom metrics"""
    global _meter
    if _meter is None:
        _meter = metrics.get_meter(__name__)
    return _meter


def setup_telemetry():
    """Setup OpenTelemetry tracing and metrics"""

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

    # Configure OTLP endpoint
    otlp_endpoint = Config.OTEL_EXPORTER_OTLP_ENDPOINT

    if otlp_endpoint:
        # Configure OTLP trace exporter
        otlp_trace_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=(
                {"Authorization": f"Bearer {Config.OTEL_EXPORTER_OTLP_HEADERS}"}
                if Config.OTEL_EXPORTER_OTLP_HEADERS
                else None
            ),
        )
        span_processor = BatchSpanProcessor(otlp_trace_exporter)
        provider.add_span_processor(span_processor)

        # Configure OTLP metric exporter
        otlp_metric_exporter = OTLPMetricExporter(
            endpoint=otlp_endpoint,
            headers=(
                {"Authorization": f"Bearer {Config.OTEL_EXPORTER_OTLP_HEADERS}"}
                if Config.OTEL_EXPORTER_OTLP_HEADERS
                else None
            ),
        )
        metric_reader = PeriodicExportingMetricReader(
            exporter=otlp_metric_exporter,
            export_interval_millis=5000,  # Export metrics every 5 seconds
        )

        # Set up meter provider
        meter_provider = MeterProvider(
            resource=resource, metric_readers=[metric_reader]
        )
        metrics.set_meter_provider(meter_provider)

        logger.info(
            f"OpenTelemetry OTLP exporters configured with endpoint: {otlp_endpoint}"
        )
    else:
        logger.info(
            "OpenTelemetry OTLP exporters not configured (OTEL_EXPORTER_OTLP_ENDPOINT not set)"
        )

    # Auto-instrument libraries
    RequestsInstrumentor().instrument()

    # Instrument system metrics (CPU, memory, disk, network)
    SystemMetricsInstrumentor().instrument()

    logger.info(
        "OpenTelemetry auto-instrumentation setup completed (including system metrics)"
    )


def instrument_fastapi_app(app: FastAPI):
    """Instrument FastAPI app with OpenTelemetry for tracing and metrics"""
    # Instrument FastAPI with both tracing and metrics
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="client/.*/info,/health,/metrics",  # Exclude health checks from tracing
    )
    logger.info("FastAPI app instrumented with OpenTelemetry (tracing and metrics)")
