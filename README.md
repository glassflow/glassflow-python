# GlassFlow Instrumentation SDK (Python)

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

glassflow.init(
    api_key="glassflow_...",          # or set GLASSFLOW_API_KEY
    service_name="my-agent",          # or set GLASSFLOW_SERVICE_NAME
)

tracer = glassflow.get_tracer()
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

