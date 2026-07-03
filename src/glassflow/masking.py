"""Export-stage PII controls: content opt-out + a redaction mask (GLA2-23).

A ``SpanExporter`` wrapper that, before spans leave the process, either strips
content attributes (``capture_content=False``) or applies a caller-supplied
``mask``. It runs on every span it sees — including third-party instrumentation —
so it's a single client-side choke point for sensitive data.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from .semconv import CONTENT_ATTRIBUTES

Mask = Callable[[Any], Any]


class MaskingSpanExporter(SpanExporter):
    """Strip or redact content attributes before delegating to ``inner``."""

    def __init__(
        self,
        inner: SpanExporter,
        *,
        capture_content: bool = True,
        mask: Mask | None = None,
    ) -> None:
        self._inner = inner
        self._capture_content = capture_content
        self._mask = mask

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        if not self._capture_content or self._mask is not None:
            for span in spans:
                self._apply(span)
        return self._inner.export(spans)

    def _apply(self, span: ReadableSpan) -> None:
        attributes: Any = getattr(span, "_attributes", None)
        if attributes is None:
            return
        keys = [key for key in CONTENT_ATTRIBUTES if key in attributes]
        if not keys:
            return
        # A span's attributes are frozen once it ends; lift the guard to edit
        # in place (this keeps the SDK's value-cleaning path), then restore it.
        was_immutable = getattr(attributes, "_immutable", False)
        if was_immutable:
            attributes._immutable = False
        try:
            for key in keys:
                if not self._capture_content:
                    del attributes[key]
                elif self._mask is not None:
                    attributes[key] = self._mask(attributes[key])
        finally:
            if was_immutable:
                attributes._immutable = True

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return self._inner.force_flush(timeout_millis)

    def shutdown(self) -> None:
        self._inner.shutdown()
