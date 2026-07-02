from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from glassflow import start_generation


def test_generation_is_llm_kind(exported_spans: InMemorySpanExporter) -> None:
    with start_generation("chat"):
        pass
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert attrs["openinference.span.kind"] == "LLM"
    assert attrs["gen_ai.operation.name"] == "chat"


def test_generation_span_name(exported_spans: InMemorySpanExporter) -> None:
    with start_generation("my-llm-call"):
        pass
    assert exported_spans.get_finished_spans()[0].name == "my-llm-call"


def test_generation_records_model_and_input(exported_spans: InMemorySpanExporter) -> None:
    with start_generation("chat", model="gpt-4o", input=[{"role": "user", "content": "hi"}]):
        pass
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert attrs["gen_ai.request.model"] == "gpt-4o"
    assert "hi" in attrs["gen_ai.input.messages"]


def test_generation_output_and_usage(exported_spans: InMemorySpanExporter) -> None:
    with start_generation("chat", model="gpt-4o") as gen:
        gen.set_output([{"role": "assistant", "content": "hello"}])
        gen.set_usage(input_tokens=10, output_tokens=5)
        gen.set_model(response_model="gpt-4o-2026-05")
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert "hello" in attrs["gen_ai.output.messages"]
    assert attrs["gen_ai.usage.input_tokens"] == 10
    assert attrs["gen_ai.usage.output_tokens"] == 5
    assert attrs["gen_ai.response.model"] == "gpt-4o-2026-05"


def test_generation_finish_reason(exported_spans: InMemorySpanExporter) -> None:
    with start_generation("chat") as gen:
        gen.set_finish_reason(["stop"])
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert attrs["gen_ai.response.finish_reasons"] == ("stop",)


def test_generation_model_parameters(exported_spans: InMemorySpanExporter) -> None:
    with start_generation("chat", model_parameters={"temperature": 0.7, "max_tokens": 256}):
        pass
    attrs = exported_spans.get_finished_spans()[0].attributes
    assert attrs["gen_ai.request.temperature"] == 0.7
    assert attrs["gen_ai.request.max_tokens"] == 256
