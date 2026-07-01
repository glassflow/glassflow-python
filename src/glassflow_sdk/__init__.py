"""GlassFlow SDK — OpenTelemetry-native tracing for AI agents and LLM apps."""

__version__ = "0.0.1"

from .client import GlassflowClient, build_span_exporter, get_tracer, init
from .config import GlassflowConfig, resolve_config

__all__ = [
    "GlassflowClient",
    "GlassflowConfig",
    "__version__",
    "build_span_exporter",
    "get_tracer",
    "init",
    "resolve_config",
]
