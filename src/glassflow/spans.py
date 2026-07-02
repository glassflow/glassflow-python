"""Low-level manual span API: a context manager plus an Observation handle.

For code that doesn't fit the `@observe` decorator. `start_generation` is the
LLM-specialized equivalent; this is the generic one.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span

from . import __version__
from ._serde import serialize
from .semconv import INPUT_VALUE, OUTPUT_VALUE, TRACER_NAME, SpanKind, set_span_kind


class Observation:
    """Handle for annotating a manually-started span."""

    def __init__(self, span: Span) -> None:
        self._span = span

    def set_input(self, value: Any) -> None:
        self._span.set_attribute(INPUT_VALUE, serialize(value))

    def set_output(self, value: Any) -> None:
        self._span.set_attribute(OUTPUT_VALUE, serialize(value))

    def set_attribute(self, key: str, value: Any) -> None:
        self._span.set_attribute(key, value)


@contextmanager
def start_span(
    name: str,
    *,
    kind: SpanKind = SpanKind.CHAIN,
    input: Any = None,
) -> Iterator[Observation]:
    """Open a span as the current span and yield an `Observation` to annotate it.

    Exceptions raised in the block are recorded and set the span status to ERROR
    (OpenTelemetry's `start_as_current_span` default), then re-raised.
    """
    tracer = trace.get_tracer(TRACER_NAME, __version__)
    with tracer.start_as_current_span(name) as span:
        set_span_kind(span, kind)
        observation = Observation(span)
        if input is not None:
            observation.set_input(input)
        yield observation
