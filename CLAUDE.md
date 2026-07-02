# CLAUDE.md — glassflow-python

Conventions for the GlassFlow instrumentation SDK (Python). Follow these; they
override generic defaults.

## What this is

A public, OpenTelemetry-native tracing SDK for AI agents / LLM applications. It
emits **OpenTelemetry GenAI (`gen_ai.*`) traces over OTLP/HTTP** to the managed
GlassFlow platform (or any OTLP-compatible backend). GlassFlow is **managed-only**
— there is no self-host, so config targets the managed endpoint.

- Distribution name: `glassflow-ai` (PyPI) · import package: `glassflow`
- `src/` layout; tests in `tests/`
- Python-first; the TS/JS SDK lives in a separate repository

## Tooling (uv-native)

```bash
uv sync --group dev       # set up the environment
uv run pytest             # tests
uv run ruff check .       # lint
uv run ruff format .      # format (use --check in CI)
uv run mypy               # type-check (strict)
uv build                  # build sdist + wheel
```

Use `uv` + `ruff` as the toolchain. Do not add pip/venv workflows or a separate
formatter/linter (no black/isort/flake8). Commit `uv.lock`.

## Code conventions

- **Python 3.10+**. Use modern typing (`X | None`, built-in generics).
- **Fully typed**; ship `py.typed`. `mypy --strict` must pass (config in `pyproject.toml`).
- **Ruff** for both lint and format; line length 100.
- Public API is re-exported from `glassflow/__init__.py` and listed in `__all__`.
- Prefer **dependency injection over mocking** for testability
  (e.g. `init(span_exporter=...)` instead of patching the OTLP exporter).

## OpenTelemetry conventions

- The canonical wire format is **OTel GenAI semantic conventions** (`gen_ai.*`).
  Do not invent bespoke attribute namespaces for things OTel already defines.
- Build on the OTel SDK primitives (`TracerProvider`, `BatchSpanProcessor`,
  OTLP/HTTP exporter). Don't hand-roll tracing internals.
- Respect OTel norms (e.g. `service.name` resource attribute).

## Testing — TDD (required)

- **Test-first.** Write a failing test, watch it fail for the right reason, then
  write minimal code to pass. No production code without a failing test first.
- pytest; use real code over mocks (inject dependencies).
- Before pushing, all gates must be green: `ruff check`, `ruff format --check`,
  `mypy`, `pytest`.

## Versioning & releases

- **Single source of truth** for the version: `__version__` in
  `src/glassflow/__init__.py` (annotated `# x-release-please-version`);
  hatchling reads it. **Do not** edit the version anywhere else or hand-write
  `CHANGELOG.md`.
- Releases are automated by **release-please** + **PyPI Trusted Publishing**
  (`.github/workflows/release.yml`). Merging the auto-generated Release PR bumps
  the version, tags `vX.Y.Z`, creates a GitHub Release, and publishes to PyPI.

## Git & PR conventions

- **Branch from `main`.** Branch names: `<user>/<TICKET>-short-desc`
  (e.g. `pablo/gla2-19-observe-decorator`). Linear team key is `GLA2`.
- **Conventional Commits are mandatory** — they drive releases:
  `feat:` (minor), `fix:` (patch), `feat!:` / `BREAKING CHANGE:` (major), plus
  `chore:`/`docs:`/`test:`/`refactor:`/`ci:`. Non-conforming commits are ignored
  for versioning.
- **No AI attribution** in commits or PRs (no `Co-Authored-By: Claude`, no
  "Generated with…" trailers).
- Open a PR; CI (lint/format/mypy + tests on Python 3.10–3.13) must pass to merge.
