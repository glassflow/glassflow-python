"""GlassFlow SDK — OpenTelemetry-native tracing for AI agents and LLM apps."""

__version__ = "0.0.1"  # x-release-please-version

from .client import GlassflowClient, build_span_exporter, get_tracer, init
from .config import GlassflowConfig, resolve_config
from .observe import observe
from .semconv import SpanKind

__all__ = [
    "GlassflowClient",
    "GlassflowConfig",
    "SpanKind",
    "__version__",
    "build_span_exporter",
    "get_tracer",
    "init",
    "observe",
    "resolve_config",
]
