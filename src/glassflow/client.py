"""SDK entrypoint: configure OpenTelemetry and export GenAI traces via OTLP."""

from __future__ import annotations

import logging
import threading
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

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_current_client: GlassflowClient | None = None


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
        self._is_shutdown = False

    def get_tracer(self, name: str = TRACER_NAME) -> trace.Tracer:
        return self._provider.get_tracer(name, __version__)

    def flush(self, timeout_millis: int = 30_000) -> bool:
        """Force-flush pending spans. Returns False on timeout."""
        return self._provider.force_flush(timeout_millis)

    def shutdown(self) -> None:
        """Drain pending spans and stop. Releases the global init() slot."""
        global _current_client
        self._provider.shutdown()
        self._is_shutdown = True
        with _lock:
            if _current_client is self:
                _current_client = None


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

    Calling ``init()`` again while a global client is active logs a warning and
    returns the existing client unchanged (the OpenTelemetry global tracer
    provider is write-once); call ``shutdown()`` on it first to reconfigure.

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
            Instrumentors are process-global, so with ``set_global=False`` they
            are only enabled when ``instruments`` is passed explicitly.
        span_exporter: Override the default OTLP exporter (useful for testing).
        set_global: Register the provider as the global OpenTelemetry provider.
    """
    global _current_client
    with _lock:
        if set_global and _current_client is not None and not _current_client._is_shutdown:
            logger.warning(
                "glassflow.init() was already called; keeping the existing configuration "
                "(the OpenTelemetry global tracer provider is write-once). Call .shutdown() "
                "on the existing client first if you need to reconfigure."
            )
            return _current_client
        return _do_init(
            endpoint=endpoint,
            api_key=api_key,
            service_name=service_name,
            headers=headers,
            disabled=disabled,
            sample_rate=sample_rate,
            capture_content=capture_content,
            mask=mask,
            instruments=instruments,
            span_exporter=span_exporter,
            set_global=set_global,
        )


def _do_init(
    *,
    endpoint: str | None,
    api_key: str | None,
    service_name: str | None,
    headers: dict[str, str] | None,
    disabled: bool | None,
    sample_rate: float | None,
    capture_content: bool | None,
    mask: Callable[[Any], Any] | None,
    instruments: Sequence[str] | None,
    span_exporter: SpanExporter | None,
    set_global: bool,
) -> GlassflowClient:
    global _current_client
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

    if set_global and not config.disabled:
        trace.set_tracer_provider(provider)
        if trace.get_tracer_provider() is not provider:
            logger.warning(
                "could not register the glassflow tracer provider as the OpenTelemetry "
                "global (another provider is already set); spans from @observe and "
                "glassflow.get_tracer() will keep using the pre-existing provider. Use "
                "the returned client's get_tracer() for scoped tracing."
            )

    # Instrumentors are process-global singletons: auto-enable only for a global
    # init; a scoped client must opt in explicitly via `instruments=[...]`.
    if not config.disabled and (set_global or instruments is not None):
        enable_instrumentations(provider, instruments)

    client = GlassflowClient(provider, config)
    if set_global:
        _current_client = client
    return client


def get_tracer(name: str = TRACER_NAME) -> trace.Tracer:
    """Return a tracer from the globally configured provider."""
    return trace.get_tracer(name, __version__)
