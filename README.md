# glassflow-sdk (Python)

OpenTelemetry-native tracing for AI agents and LLM applications. `glassflow-sdk`
emits [OpenTelemetry GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
traces over OTLP to the managed GlassFlow observability platform (or any
OTLP-compatible backend).

> Status: alpha. APIs may change.

## Install

```bash
pip install glassflow-sdk
```

## Quickstart

```python
import glassflow_sdk

glassflow_sdk.init(
    api_key="glassflow_...",          # or set GLASSFLOW_API_KEY
    service_name="my-agent",          # or set GLASSFLOW_SERVICE_NAME
)

tracer = glassflow_sdk.get_tracer()
with tracer.start_as_current_span("my-operation"):
    ...
```

Configuration is resolved from explicit arguments first, then environment
variables:

| Argument       | Environment variable     | Default                        | Description                                                          |
| -------------- | ------------------------ | ------------------------------ | -------------------------------------------------------------------- |
| `endpoint`     | `GLASSFLOW_ENDPOINT`     | `https://ingest.glassflow.dev` | Base OTLP endpoint. Traces are sent to `<endpoint>/v1/traces`.       |
| `api_key`      | `GLASSFLOW_API_KEY`      | —                              | Injected as an `Authorization: Bearer <key>` header on every export. |
| `service_name` | `GLASSFLOW_SERVICE_NAME` | `unknown_service`              | Sets the OpenTelemetry `service.name` resource attribute.            |
| `disabled`     | `GLASSFLOW_DISABLED`     | `false`                        | Kill switch. When true, spans are created but never exported.        |

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

## License

MIT
