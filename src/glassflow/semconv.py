"""Semantic conventions for the GlassFlow SDK.

Centralizes the OpenTelemetry instrumentation-scope name, the span-kind taxonomy,
and span attribute keys. Span kinds use the OpenInference `openinference.span.kind`
values (understood across the ecosystem); LLM specifics use OTel GenAI `gen_ai.*`.
"""

from __future__ import annotations

from enum import Enum

from opentelemetry.trace import Span

# Instrumentation scope name (stamped on every span as otel.scope.name).
TRACER_NAME = "glassflow"

# --- Attribute keys ---
# OpenInference
OPENINFERENCE_SPAN_KIND = "openinference.span.kind"
INPUT_VALUE = "input.value"
OUTPUT_VALUE = "output.value"

# OTel GenAI (subset we emit)
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
GEN_AI_PROVIDER_NAME = "gen_ai.provider.name"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
GEN_AI_INPUT_MESSAGES = "gen_ai.input.messages"
GEN_AI_OUTPUT_MESSAGES = "gen_ai.output.messages"
GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
GEN_AI_REQUEST_PREFIX = "gen_ai.request."


class SpanKind(str, Enum):
    """Observation kind. Values are OpenInference `openinference.span.kind` values."""

    AGENT = "AGENT"
    LLM = "LLM"
    TOOL = "TOOL"
    RETRIEVER = "RETRIEVER"
    EMBEDDING = "EMBEDDING"
    CHAIN = "CHAIN"  # generic processing step (OpenInference's general-purpose kind)


# SpanKind -> OTel GenAI gen_ai.operation.name, where a canonical operation exists.
_OPERATION_BY_KIND: dict[SpanKind, str] = {
    SpanKind.LLM: "chat",
    SpanKind.TOOL: "execute_tool",
    SpanKind.EMBEDDING: "embeddings",
    SpanKind.AGENT: "invoke_agent",
}


def set_span_kind(span: Span, kind: SpanKind) -> None:
    """Stamp a span with its OpenInference kind and (if applicable) gen_ai operation."""
    span.set_attribute(OPENINFERENCE_SPAN_KIND, kind.value)
    operation = _OPERATION_BY_KIND.get(kind)
    if operation is not None:
        span.set_attribute(GEN_AI_OPERATION_NAME, operation)
