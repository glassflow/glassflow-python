"""Shared constants for the GlassFlow SDK.

Centralizes the OpenTelemetry instrumentation-scope name and span attribute keys
so they are defined once and used consistently. The attribute keys are the seed
of a fuller semantic-conventions module (see GLA2-21).
"""

# OpenTelemetry instrumentation scope name (stamped on every span as otel.scope.name).
# A single fixed constant is the OTel-recommended approach (over per-module __name__).
TRACER_NAME = "glassflow"

# Generic function-I/O span attribute keys captured by @observe.
# Typed gen_ai.* conventions are added in GLA2-21.
INPUT_ATTR = "glassflow.input"
OUTPUT_ATTR = "glassflow.output"
