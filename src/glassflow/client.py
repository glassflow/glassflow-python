"""SDK entrypoint: configure OpenTelemetry and export GenAI traces via OTLP."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from . import __version__
from .config import GlassflowConfig, resolve_config
from .instrumentation import enable_instrumentations
from .masking import MaskingSpanExporter
from .semconv import TRACER_NAME


def build_span_exporter(config: GlassflowConfig) -> SpanExporter:
    """Build the default OTLP/HTTP span exporter for a resolved config."""
    return OTLPSpanExporter(
        endpoint=config.traces_endpoint,
        headers=config.headers or None,
    )


class GlassflowClient:
    """Handle over a configured tracer provider."""

    def __init__(self, provider: TracerProvider, config: GlassflowConfig) -> None:
        self._provider = provider
        self.config = config

    def get_tracer(self, name: str = TRACER_NAME) -> trace.Tracer:
        return self._provider.get_tracer(name, __version__)

    def flush(self, timeout_millis: int = 30_000) -> bool:
        """Force-flush pending spans. Returns False on timeout."""
        return self._provider.force_flush(timeout_millis)

    def shutdown(self) -> None:
        self._provider.shutdown()


def init(
    *,
    endpoint: str | None = None,
    api_key: str | None = None,
    service_name: str | None = None,
    headers: dict[str, str] | None = None,
    disabled: bool | None = None,
    sample_rate: float | None = None,
    capture_content: bool | None = None,
    mask: Callable[[Any], Any] | None = None,
    instruments: Sequence[str] | None = None,
    span_exporter: SpanExporter | None = None,
    set_global: bool = True,
) -> GlassflowClient:
    """Initialize the SDK: build a tracer provider that exports OTLP traces.

    Args:
        endpoint: Base OTLP endpoint. Traces are sent to ``<endpoint>/v1/traces``.
        api_key: API key; injected as an ``Authorization: Bearer`` header.
        service_name: Value for the ``service.name`` resource attribute.
        headers: Extra headers for the OTLP exporter.
        disabled: If True, no exporter is attached (spans are dropped).
        sample_rate: Head sampling ratio 0.0-1.0 (whole-trace). Default 1.0.
        capture_content: If False, strip prompt/response content at export. Default True.
        mask: Redact content attribute values at export (applies to all spans).
        instruments: Auto-instrumentation selection. ``None`` (default) enables
            every bundled instrumentor whose package is installed; a list
            restricts to those names; ``[]`` disables auto-instrumentation.
        span_exporter: Override the default OTLP exporter (useful for testing).
        set_global: Register the provider as the global OpenTelemetry provider.
    """
    config = resolve_config(
        endpoint=endpoint,
        api_key=api_key,
        service_name=service_name,
        headers=headers,
        disabled=disabled,
        sample_rate=sample_rate,
        capture_content=capture_content,
    )
    resource = Resource.create(
        {
            "service.name": config.service_name,
            "telemetry.sdk.name": "glassflow-ai",
            "telemetry.sdk.version": __version__,
            "telemetry.sdk.language": "python",
        }
    )
    sampler = ParentBased(root=TraceIdRatioBased(config.sample_rate))
    provider = TracerProvider(resource=resource, sampler=sampler)

    if not config.disabled:
        exporter = span_exporter if span_exporter is not None else build_span_exporter(config)
        if not config.capture_content or mask is not None:
            exporter = MaskingSpanExporter(
                exporter, capture_content=config.capture_content, mask=mask
            )
        provider.add_span_processor(BatchSpanProcessor(exporter))

    if set_global:
        trace.set_tracer_provider(provider)

    if not config.disabled:
        enable_instrumentations(provider, instruments)

    return GlassflowClient(provider, config)


def get_tracer(name: str = TRACER_NAME) -> trace.Tracer:
    """Return a tracer from the globally configured provider."""
    return trace.get_tracer(name, __version__)
