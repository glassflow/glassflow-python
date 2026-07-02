"""LLM generation capture helpers.

`start_generation` opens an LLM-kind span and returns a `Generation` handle for
recording gen_ai-native attributes (messages, model, usage, finish reason). LLM
spans are therefore readable by any gen_ai-compatible consumer.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span

from . import __version__
from .semconv import (
    GEN_AI_INPUT_MESSAGES,
    GEN_AI_OUTPUT_MESSAGES,
    GEN_AI_REQUEST_MODEL,
    GEN_AI_REQUEST_PREFIX,
    GEN_AI_RESPONSE_FINISH_REASONS,
    GEN_AI_RESPONSE_MODEL,
    GEN_AI_SYSTEM,
    GEN_AI_USAGE_INPUT_TOKENS,
    GEN_AI_USAGE_OUTPUT_TOKENS,
    TRACER_NAME,
    SpanKind,
    set_span_kind,
)

Messages = str | list[Any]


def _serialize_messages(messages: Messages) -> str:
    if isinstance(messages, str):
        return messages
    return json.dumps(messages, default=repr)


class Generation:
    """Handle for recording gen_ai attributes on an LLM span."""

    def __init__(self, span: Span) -> None:
        self._span = span

    def set_input(self, messages: Messages) -> None:
        self._span.set_attribute(GEN_AI_INPUT_MESSAGES, _serialize_messages(messages))

    def set_output(self, messages: Messages) -> None:
        self._span.set_attribute(GEN_AI_OUTPUT_MESSAGES, _serialize_messages(messages))

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


@contextmanager
def start_generation(
    name: str,
    *,
    model: str | None = None,
    system: str | None = None,
    input: Messages | None = None,
    model_parameters: dict[str, Any] | None = None,
) -> Iterator[Generation]:
    """Open an LLM-kind span and yield a `Generation` handle for gen_ai attributes."""
    tracer = trace.get_tracer(TRACER_NAME, __version__)
    with tracer.start_as_current_span(name) as span:
        set_span_kind(span, SpanKind.LLM)
        if model is not None:
            span.set_attribute(GEN_AI_REQUEST_MODEL, model)
        if system is not None:
            span.set_attribute(GEN_AI_SYSTEM, system)
        for key, value in (model_parameters or {}).items():
            span.set_attribute(f"{GEN_AI_REQUEST_PREFIX}{key}", value)
        generation = Generation(span)
        if input is not None:
            generation.set_input(input)
        yield generation
