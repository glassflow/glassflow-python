"""First-class MCP tool-call spans (client side: ClientSession.call_tool)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

pytest.importorskip("mcp")

from mcp.server.fastmcp import FastMCP  # noqa: E402
from mcp.shared.memory import create_connected_server_and_client_session  # noqa: E402

from glassflow import init  # noqa: E402
from glassflow.instrumentation import REGISTRY  # noqa: E402
from glassflow.instrumentation_mcp import MCPInstrumentor  # noqa: E402


def _make_server() -> FastMCP:
    server = FastMCP("test-server")

    @server.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @server.tool()
    def boom() -> str:
        """Always fails."""
        raise ValueError("tool failed")

    return server


@pytest.fixture(autouse=True)
def _fresh_mcp_instrumentor() -> Any:
    instrumentor = MCPInstrumentor()
    if instrumentor.is_instrumented_by_opentelemetry:
        instrumentor.uninstrument()
    yield
    if instrumentor.is_instrumented_by_opentelemetry:
        instrumentor.uninstrument()


def _run_tool_call(
    tool: str,
    arguments: dict[str, Any] | None,
    **init_kwargs: Any,
) -> tuple[list[ReadableSpan], Any]:
    inner = InMemorySpanExporter()
    client = init(span_exporter=inner, set_global=False, instruments=["mcp"], **init_kwargs)

    async def scenario() -> Any:
        server = _make_server()
        async with create_connected_server_and_client_session(server._mcp_server) as session:
            return await session.call_tool(tool, arguments)

    result = asyncio.run(scenario())
    client.flush()
    return list(inner.get_finished_spans()), result


def test_mcp_is_a_registry_instrument() -> None:
    assert "mcp" in {spec.name for spec in REGISTRY}


def test_call_tool_creates_tool_span() -> None:
    spans, _result = _run_tool_call("add", {"a": 2, "b": 3})
    tool_spans = [s for s in spans if s.name == "execute_tool add"]
    assert tool_spans, f"no tool span; got {[s.name for s in spans]}"
    attrs = tool_spans[0].attributes
    assert attrs is not None
    assert attrs["openinference.span.kind"] == "TOOL"
    assert attrs["gen_ai.operation.name"] == "execute_tool"
    assert attrs["gen_ai.tool.name"] == "add"
    assert json.loads(attrs["input.value"]) == {"a": 2, "b": 3}
    assert "5" in attrs["output.value"]


def test_tool_error_result_marks_span_error() -> None:
    spans, result = _run_tool_call("boom", None)
    assert result.isError  # FastMCP converts tool exceptions into error results
    (tool_span,) = [s for s in spans if s.name == "execute_tool boom"]
    assert not tool_span.status.is_ok


def test_tool_span_nests_under_current_span() -> None:
    inner = InMemorySpanExporter()
    client = init(span_exporter=inner, set_global=False, instruments=["mcp"])

    async def scenario() -> None:
        server = _make_server()
        with client.get_tracer().start_as_current_span("agent-step"):
            async with create_connected_server_and_client_session(server._mcp_server) as session:
                await session.call_tool("add", {"a": 1, "b": 1})

    asyncio.run(scenario())
    client.flush()
    spans = {s.name: s for s in inner.get_finished_spans()}
    tool_span = spans["execute_tool add"]
    assert tool_span.parent is not None
    assert tool_span.parent.span_id == spans["agent-step"].context.span_id


def test_capture_content_false_strips_tool_io_but_keeps_tool_name() -> None:
    spans, _result = _run_tool_call("add", {"a": 2, "b": 3}, capture_content=False)
    (tool_span,) = [s for s in spans if s.name == "execute_tool add"]
    attrs = tool_span.attributes
    assert attrs is not None
    assert "input.value" not in attrs
    assert "output.value" not in attrs
    assert attrs["gen_ai.tool.name"] == "add"


def test_uninstrument_restores_call_tool() -> None:
    spans, _result = _run_tool_call("add", {"a": 1, "b": 2})
    assert any(s.name == "execute_tool add" for s in spans)

    MCPInstrumentor().uninstrument()

    inner = InMemorySpanExporter()
    client = init(span_exporter=inner, set_global=False)  # scoped, no instruments

    async def scenario() -> None:
        server = _make_server()
        async with create_connected_server_and_client_session(server._mcp_server) as session:
            await session.call_tool("add", {"a": 1, "b": 2})

    asyncio.run(scenario())
    client.flush()
    assert not any(s.name.startswith("execute_tool") for s in inner.get_finished_spans())
