import asyncio

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from glassflow import observe
from glassflow.semconv import SpanKind


@observe
def add(a: int, b: int) -> int:
    return a + b


@observe(name="custom-name")
def named() -> str:
    return "ok"


@observe
def boom() -> None:
    raise ValueError("nope")


@observe
async def async_add(a: int, b: int) -> int:
    return a + b


@observe
def gen(n: int):
    yield from range(n)


@observe(capture_input=False, capture_output=False)
def secret(password: str) -> str:
    return "redacted-return"


@observe
def outer() -> int:
    return add(1, 2)


def test_sync_span_named_after_function(exported_spans: InMemorySpanExporter) -> None:
    assert add(2, 3) == 5
    spans = exported_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "add"


def test_custom_name(exported_spans: InMemorySpanExporter) -> None:
    named()
    assert exported_spans.get_finished_spans()[0].name == "custom-name"


def test_captures_input_and_output(exported_spans: InMemorySpanExporter) -> None:
    add(2, 3)
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert "2" in attrs["input.value"] and "3" in attrs["input.value"]
    assert attrs["output.value"] == "5"


def test_exception_records_error_and_reraises(exported_spans: InMemorySpanExporter) -> None:
    with pytest.raises(ValueError, match="nope"):
        boom()
    span = exported_spans.get_finished_spans()[0]
    assert span.status.status_code == StatusCode.ERROR
    assert any(e.name == "exception" for e in span.events)


def test_async_function(exported_spans: InMemorySpanExporter) -> None:
    assert asyncio.run(async_add(2, 3)) == 5
    assert exported_spans.get_finished_spans()[0].name == "async_add"


def test_generator_spans_iteration(exported_spans: InMemorySpanExporter) -> None:
    assert list(gen(3)) == [0, 1, 2]
    spans = exported_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "gen"


def test_capture_flags_disable_io(exported_spans: InMemorySpanExporter) -> None:
    secret("hunter2")
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert "input.value" not in attrs
    assert "output.value" not in attrs


def test_default_kind_is_chain(exported_spans: InMemorySpanExporter) -> None:
    add(1, 1)
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert attrs["openinference.span.kind"] == "CHAIN"


def test_kind_override(exported_spans: InMemorySpanExporter) -> None:
    @observe(kind=SpanKind.TOOL)
    def search(q: str) -> str:
        return "result"

    search("hi")
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert attrs["openinference.span.kind"] == "TOOL"


def test_nested_spans_have_parent(exported_spans: InMemorySpanExporter) -> None:
    assert outer() == 3
    spans = {s.name: s for s in exported_spans.get_finished_spans()}
    assert set(spans) == {"outer", "add"}
    assert spans["add"].parent.span_id == spans["outer"].context.span_id


class Service:
    @observe
    def work(self, x: int) -> int:
        return x * 2


@observe
async def agen(n: int):
    for i in range(n):
        yield i


def test_method_target(exported_spans: InMemorySpanExporter) -> None:
    assert Service().work(21) == 42
    assert exported_spans.get_finished_spans()[0].name == "Service.work"


def test_async_generator(exported_spans: InMemorySpanExporter) -> None:
    async def consume() -> list[int]:
        return [i async for i in agen(3)]

    assert asyncio.run(consume()) == [0, 1, 2]
    spans = exported_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "agen"
