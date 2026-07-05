"""LLM generation capture helpers.

``start_as_current_generation`` (context manager) and ``start_generation`` (manual,
requires ``.end()``) open an LLM-kind span and return a ``Generation`` handle for
recording gen_ai-native attributes (messages, model, usage, finish reason). LLM
spans are therefore readable by any gen_ai-compatible consumer.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span

from . import __version__
from ._serde import serialize
from .semconv import (
    GEN_AI_INPUT_MESSAGES,
    GEN_AI_OUTPUT_MESSAGES,
    GEN_AI_PROVIDER_NAME,
    GEN_AI_REQUEST_MODEL,
    GEN_AI_REQUEST_PREFIX,
    GEN_AI_RESPONSE_FINISH_REASONS,
    GEN_AI_RESPONSE_MODEL,
    GEN_AI_USAGE_INPUT_TOKENS,
    GEN_AI_USAGE_OUTPUT_TOKENS,
    TRACER_NAME,
    SpanKind,
    set_span_kind,
)

Messages = str | list[Any]


def _normalize_part(item: Any) -> dict[str, Any]:
    """Convert one content-list entry into a spec message part."""
    if isinstance(item, dict):
        # OpenAI multimodal text part {"type": "text", "text": ...}
        if item.get("type") == "text" and "text" in item:
            return {"type": "text", "content": item["text"]}
        if "type" in item:
            return item  # already-typed part: pass through
    return {"type": "text", "content": item if isinstance(item, str) else serialize(item)}


def _normalize_message(message: Any, default_role: str) -> dict[str, Any]:
    """Convert one message into the spec ``{"role", "parts": [...]}`` shape.

    Accepts spec-conformant messages (passed through), OpenAI-style
    ``{"role", "content"}`` / ``tool_calls`` / tool-response messages, and
    falls back to a serialized text part for anything else.
    """
    if isinstance(message, str):
        return {"role": default_role, "parts": [{"type": "text", "content": message}]}
    if not isinstance(message, dict):
        return {"role": default_role, "parts": [{"type": "text", "content": serialize(message)}]}
    if "parts" in message:
        normalized = dict(message)
        normalized.setdefault("role", default_role)
        return normalized

    role = message.get("role", default_role)
    if role == "tool" and "tool_call_id" in message:
        return {
            "role": "tool",
            "parts": [
                {
                    "type": "tool_call_response",
                    "id": message["tool_call_id"],
                    "response": message.get("content"),
                }
            ],
        }

    parts: list[dict[str, Any]] = []
    content = message.get("content")
    if isinstance(content, str):
        parts.append({"type": "text", "content": content})
    elif isinstance(content, list):
        parts.extend(_normalize_part(item) for item in content)
    elif content is not None:
        parts.append({"type": "text", "content": serialize(content)})
    for call in message.get("tool_calls") or []:
        if isinstance(call, dict):
            function = call.get("function") or {}
            parts.append(
                {
                    "type": "tool_call",
                    "id": call.get("id"),
                    "name": function.get("name"),
                    "arguments": function.get("arguments"),
                }
            )
    return {"role": role, "parts": parts}


def _serialize_messages(messages: Messages, default_role: str) -> str:
    """Serialize to the spec message-array shape (JSON string attribute)."""
    if isinstance(messages, str):
        normalized = [_normalize_message(messages, default_role)]
    else:
        normalized = [_normalize_message(message, default_role) for message in messages]
    return serialize(normalized)


class Generation:
    """Handle for recording gen_ai attributes on an LLM span."""

    def __init__(self, span: Span) -> None:
        self._span = span

    def set_input(self, messages: Messages) -> None:
        self._span.set_attribute(GEN_AI_INPUT_MESSAGES, _serialize_messages(messages, "user"))

    def set_output(self, messages: Messages) -> None:
        self._span.set_attribute(GEN_AI_OUTPUT_MESSAGES, _serialize_messages(messages, "assistant"))

    def set_model(self, response_model: str) -> None:
        self._span.set_attribute(GEN_AI_RESPONSE_MODEL, response_model)

    def set_usage(
        self, *, input_tokens: int | None = None, output_tokens: int | None = None
    ) -> None:
        if input_tokens is not None:
            self._span.set_attribute(GEN_AI_USAGE_INPUT_TOKENS, input_tokens)
        if output_tokens is not None:
            self._span.set_attribute(GEN_AI_USAGE_OUTPUT_TOKENS, output_tokens)

    def set_finish_reason(self, reasons: list[str]) -> None:
        self._span.set_attribute(GEN_AI_RESPONSE_FINISH_REASONS, reasons)

    def update(self, *, input: Messages | None = None, output: Messages | None = None) -> None:
        if input is not None:
            self.set_input(input)
        if output is not None:
            self.set_output(output)

    def end(self) -> None:
        self._span.end()


def _configure(
    generation: Generation,
    *,
    model: str | None,
    provider: str | None,
    input: Messages | None,
    model_parameters: dict[str, Any] | None,
) -> None:
    span = generation._span
    set_span_kind(span, SpanKind.LLM)
    if model is not None:
        span.set_attribute(GEN_AI_REQUEST_MODEL, model)
    if provider is not None:
        span.set_attribute(GEN_AI_PROVIDER_NAME, provider)
    for key, value in (model_parameters or {}).items():
        span.set_attribute(f"{GEN_AI_REQUEST_PREFIX}{key}", value)
    if input is not None:
        generation.set_input(input)


def start_generation(
    name: str,
    *,
    model: str | None = None,
    provider: str | None = None,
    input: Messages | None = None,
    model_parameters: dict[str, Any] | None = None,
) -> Generation:
    """Create an LLM-kind span and return a ``Generation``. You MUST call ``.end()``.

    Manual counterpart to ``start_as_current_generation``: not set as current, no
    auto-recording of exceptions.
    """
    span = trace.get_tracer(TRACER_NAME, __version__).start_span(name)
    generation = Generation(span)
    _configure(
        generation, model=model, provider=provider, input=input, model_parameters=model_parameters
    )
    return generation


@contextmanager
def start_as_current_generation(
    name: str,
    *,
    model: str | None = None,
    provider: str | None = None,
    input: Messages | None = None,
    model_parameters: dict[str, Any] | None = None,
) -> Iterator[Generation]:
    """Open an LLM-kind span as the current span and yield a ``Generation``; auto-ends."""
    tracer = trace.get_tracer(TRACER_NAME, __version__)
    with tracer.start_as_current_span(name) as span:
        generation = Generation(span)
        _configure(
            generation,
            model=model,
            provider=provider,
            input=input,
            model_parameters=model_parameters,
        )
        yield generation
