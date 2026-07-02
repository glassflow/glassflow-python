"""GlassFlow SDK — OpenTelemetry-native tracing for AI agents and LLM apps."""

__version__ = "0.0.1"  # x-release-please-version

from .client import GlassflowClient, build_span_exporter, get_tracer, init
from .config import GlassflowConfig, resolve_config
from .generation import Generation, start_generation
from .observe import observe
from .semconv import SpanKind
from .spans import Observation, start_span

__all__ = [
    "Generation",
    "GlassflowClient",
    "GlassflowConfig",
    "Observation",
    "SpanKind",
    "__version__",
    "build_span_exporter",
    "get_tracer",
    "init",
    "observe",
    "resolve_config",
    "start_generation",
    "start_span",
]
