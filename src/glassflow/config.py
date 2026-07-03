"""Configuration resolution for the GlassFlow SDK.

Values are resolved with the precedence: explicit arguments > environment
variables > built-in defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_ENDPOINT = "https://ingest.glassflow.dev"
DEFAULT_SERVICE_NAME = "unknown_service"

ENV_ENDPOINT = "GLASSFLOW_ENDPOINT"
ENV_API_KEY = "GLASSFLOW_API_KEY"
ENV_SERVICE_NAME = "GLASSFLOW_SERVICE_NAME"
ENV_DISABLED = "GLASSFLOW_DISABLED"
ENV_SAMPLE_RATE = "GLASSFLOW_SAMPLE_RATE"

_TRUENESS = frozenset({"1", "true", "yes", "on"})


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUENESS


def _env_float(name: str, *, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class GlassflowConfig:
    """Resolved, immutable SDK configuration."""

    endpoint: str
    api_key: str | None
    service_name: str
    headers: dict[str, str] = field(default_factory=dict)
    disabled: bool = False
    sample_rate: float = 1.0

    @property
    def traces_endpoint(self) -> str:
        """Full OTLP/HTTP traces URL (``<endpoint>/v1/traces``)."""
        return self.endpoint.rstrip("/") + "/v1/traces"


def resolve_config(
    *,
    endpoint: str | None = None,
    api_key: str | None = None,
    service_name: str | None = None,
    headers: dict[str, str] | None = None,
    disabled: bool | None = None,
    sample_rate: float | None = None,
) -> GlassflowConfig:
    """Resolve SDK configuration from arguments, environment, then defaults."""
    resolved_endpoint = endpoint or os.getenv(ENV_ENDPOINT) or DEFAULT_ENDPOINT
    resolved_api_key = api_key if api_key is not None else os.getenv(ENV_API_KEY)
    resolved_service_name = service_name or os.getenv(ENV_SERVICE_NAME) or DEFAULT_SERVICE_NAME
    resolved_disabled = _env_bool(ENV_DISABLED, default=False) if disabled is None else disabled
    resolved_sample_rate = (
        _env_float(ENV_SAMPLE_RATE, default=1.0) if sample_rate is None else sample_rate
    )

    resolved_headers = dict(headers or {})
    has_auth = any(key.lower() == "authorization" for key in resolved_headers)
    if resolved_api_key and not has_auth:
        resolved_headers["Authorization"] = f"Bearer {resolved_api_key}"

    return GlassflowConfig(
        endpoint=resolved_endpoint,
        api_key=resolved_api_key,
        service_name=resolved_service_name,
        headers=resolved_headers,
        disabled=resolved_disabled,
        sample_rate=resolved_sample_rate,
    )
