# GlassFlow Python SDK

OpenTelemetry-native tracing for AI agents and LLM applications. `glassflow-ai`
emits [OpenTelemetry GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
traces over OTLP to the managed GlassFlow observability platform (or any
OTLP-compatible backend).

> Status: alpha. APIs may change.

## Install

```bash
pip install glassflow-ai
```

## Quickstart

```python
import glassflow
from glassflow import observe, start_as_current_generation, start_as_current_span
from glassflow.semconv import SpanKind

glassflow.init(
    api_key="glassflow_...",          # or set GLASSFLOW_API_KEY
    service_name="my-agent",          # or set GLASSFLOW_SERVICE_NAME
)

# 1. Decorator — trace a whole function
@observe
def handle(query: str) -> str: ...

# 2. Context manager — trace a block
with start_as_current_span("retrieve", kind=SpanKind.RETRIEVER) as obs:
    obs.set_output(docs)

# 3. LLM generations — gen_ai-native
with start_as_current_generation("chat", model="gpt-4o", input=messages) as gen:
    gen.set_output(reply)
    gen.set_usage(input_tokens=42, output_tokens=17)
```

Each surface has a **manual** variant for lifetimes a `with` block can't express
(streaming, callbacks): `start_span(...)` / `start_generation(...)` return a handle
you `.update()` and must `.end()` yourself.

Configuration is resolved from explicit arguments first, then environment
variables:

| Argument       | Environment variable     | Default                        | Description                                                          |
| -------------- | ------------------------ | ------------------------------ | -------------------------------------------------------------------- |
| `endpoint`     | `GLASSFLOW_ENDPOINT`     | `https://ingest.glassflow.dev` | Base OTLP endpoint. Traces are sent to `<endpoint>/v1/traces`.       |
| `api_key`      | `GLASSFLOW_API_KEY`      | —                              | Injected as an `Authorization: Bearer <key>` header on every export. |
| `service_name` | `GLASSFLOW_SERVICE_NAME` | `unknown_service`              | Sets the OpenTelemetry `service.name` resource attribute.            |
| `disabled`     | `GLASSFLOW_DISABLED`     | `false`                        | Kill switch. When true, spans are created but never exported.        |
| `sample_rate`  | `GLASSFLOW_SAMPLE_RATE`  | `1.0`                          | Head sampling ratio `0.0`–`1.0` (whole-trace; children follow root). |

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

## Releasing

Releases are automated with [release-please](https://github.com/googleapis/release-please)
and published to PyPI via Trusted Publishing.

1. Merge changes to `main` using [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat:` → minor, `fix:` → patch, `feat!:`/`BREAKING CHANGE` → major).
2. release-please keeps a **Release PR** open that bumps `__version__` and updates
   `CHANGELOG.md`. Merge it when you want to cut a release.
3. Merging tags `vX.Y.Z`, creates a GitHub Release, and publishes to PyPI automatically.

Non-conventional commits are ignored for versioning.

## License

MIT

