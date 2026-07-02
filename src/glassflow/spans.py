"""Manual span API.

Two surfaces, following the OpenTelemetry / Langfuse / Laminar convention:

- ``start_as_current_span`` — context manager: activates the span in the OTel
  context (so children nest under it) and auto-ends it.
- ``start_span`` — manual: returns an ``Observation`` you must ``.end()``. The span
  is parented to the current span at creation but is NOT set as current and does
  NOT auto-record exceptions. For lifetimes a ``with`` block can't express
  (streaming, callbacks, passing a span across boundaries).

``start_generation`` / ``start_as_current_generation`` are the LLM-specialized
equivalents.
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
    """Handle for annotating a span."""

    def __init__(self, span: Span) -> None:
        self._span = span

    def set_input(self, value: Any) -> None:
        self._span.set_attribute(INPUT_VALUE, serialize(value))

    def set_output(self, value: Any) -> None:
        self._span.set_attribute(OUTPUT_VALUE, serialize(value))

    def set_attribute(self, key: str, value: Any) -> None:
        self._span.set_attribute(key, value)

    def update(self, *, input: Any = None, output: Any = None) -> None:
        if input is not None:
            self.set_input(input)
        if output is not None:
            self.set_output(output)

    def end(self) -> None:
        self._span.end()


def _configure(observation: Observation, kind: SpanKind, input: Any) -> None:
    set_span_kind(observation._span, kind)
    if input is not None:
        observation.set_input(input)


def start_span(name: str, *, kind: SpanKind = SpanKind.CHAIN, input: Any = None) -> Observation:
    """Create a span and return an ``Observation``. You MUST call ``.end()``.

    The span is parented to the current span at creation, but is not set as the
    current span and does not auto-record exceptions. Use ``start_as_current_span``
    for block-scoped tracing.
    """
    span = trace.get_tracer(TRACER_NAME, __version__).start_span(name)
    observation = Observation(span)
    _configure(observation, kind, input)
    return observation


@contextmanager
def start_as_current_span(
    name: str,
    *,
    kind: SpanKind = SpanKind.CHAIN,
    input: Any = None,
) -> Iterator[Observation]:
    """Open a span as the current span and yield an ``Observation``; auto-ends.

    Exceptions raised in the block are recorded and set the span status to ERROR
    (OpenTelemetry's ``start_as_current_span`` default), then re-raised.
    """
    tracer = trace.get_tracer(TRACER_NAME, __version__)
    with tracer.start_as_current_span(name) as span:
        observation = Observation(span)
        _configure(observation, kind, input)
        yield observation
