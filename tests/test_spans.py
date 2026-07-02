import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from glassflow import start_span
from glassflow.semconv import SpanKind


def test_default_kind_is_chain(exported_spans: InMemorySpanExporter) -> None:
    with start_span("step"):
        pass
    span = exported_spans.get_finished_spans()[0]
    assert span.name == "step"
    assert span.attributes["openinference.span.kind"] == "CHAIN"


def test_custom_kind(exported_spans: InMemorySpanExporter) -> None:
    with start_span("t", kind=SpanKind.TOOL):
        pass
    assert exported_spans.get_finished_spans()[0].attributes["openinference.span.kind"] == "TOOL"


def test_input_and_output(exported_spans: InMemorySpanExporter) -> None:
    with start_span("s", input={"q": "hi"}) as obs:
        obs.set_output(["a", "b"])
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert "hi" in attrs["input.value"]
    assert "a" in attrs["output.value"]


def test_set_attribute(exported_spans: InMemorySpanExporter) -> None:
    with start_span("s") as obs:
        obs.set_attribute("custom.tag", "x")
    assert exported_spans.get_finished_spans()[0].attributes["custom.tag"] == "x"


def test_nesting(exported_spans: InMemorySpanExporter) -> None:
    # entered left-to-right, so "inner" nests under "outer"
    with start_span("outer"), start_span("inner"):
        pass
    spans = {s.name: s for s in exported_spans.get_finished_spans()}
    assert spans["inner"].parent.span_id == spans["outer"].context.span_id


def test_exception_sets_error_status(exported_spans: InMemorySpanExporter) -> None:
    with pytest.raises(ValueError, match="boom"), start_span("op"):
        raise ValueError("boom")
    span = exported_spans.get_finished_spans()[0]
    assert span.status.status_code == StatusCode.ERROR
    assert any(e.name == "exception" for e in span.events)
