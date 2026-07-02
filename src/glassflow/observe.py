"""The `@observe` decorator: trace the developer's own functions.

Wraps sync, async, generator, and async-generator functions (and methods),
recording timing, inputs/outputs, and exceptions as an OpenTelemetry span.
Spans nest automatically via OTel context propagation and are exported through
whatever provider `init()` configured (a no-op if the SDK was never initialized).
"""

from __future__ import annotations

import functools
import inspect
import json
from collections.abc import Callable
from typing import Any, TypeVar, overload

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from . import __version__
from ._constants import INPUT_ATTR, OUTPUT_ATTR, TRACER_NAME

_MAX_ATTR_CHARS = 8192

F = TypeVar("F", bound=Callable[..., Any])


def _serialize(value: Any) -> str:
    try:
        text = json.dumps(value, default=repr)
    except (TypeError, ValueError):
        text = repr(value)
    if len(text) > _MAX_ATTR_CHARS:
        text = text[:_MAX_ATTR_CHARS] + "…(truncated)"
    return text


def _serialize_inputs(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    return _serialize({"args": args, "kwargs": kwargs})


def _record_exception(span: trace.Span, exc: BaseException) -> None:
    span.record_exception(exc)
    span.set_status(Status(StatusCode.ERROR, str(exc)))


@overload
def observe(func: F) -> F: ...


@overload
def observe(
    *,
    name: str | None = ...,
    capture_input: bool = ...,
    capture_output: bool = ...,
) -> Callable[[F], F]: ...


def observe(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    capture_input: bool = True,
    capture_output: bool = True,
) -> Any:
    """Decorate a function so each call is traced as a span.

    Usable bare (`@observe`) or parameterized (`@observe(name=..., ...)`).
    """

    def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        span_name = name or fn.__qualname__

        def _set_input(span: trace.Span, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
            if capture_input:
                span.set_attribute(INPUT_ATTR, _serialize_inputs(args, kwargs))

        def _set_output(span: trace.Span, result: Any) -> None:
            if capture_output:
                span.set_attribute(OUTPUT_ATTR, _serialize(result))

        if inspect.isasyncgenfunction(fn):

            @functools.wraps(fn)
            async def async_gen_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = trace.get_tracer(TRACER_NAME, __version__)
                with tracer.start_as_current_span(span_name) as span:
                    _set_input(span, args, kwargs)
                    try:
                        async for item in fn(*args, **kwargs):
                            yield item
                    except Exception as exc:
                        _record_exception(span, exc)
                        raise

            return async_gen_wrapper

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = trace.get_tracer(TRACER_NAME, __version__)
                with tracer.start_as_current_span(span_name) as span:
                    _set_input(span, args, kwargs)
                    try:
                        result = await fn(*args, **kwargs)
                    except Exception as exc:
                        _record_exception(span, exc)
                        raise
                    _set_output(span, result)
                    return result

            return async_wrapper

        if inspect.isgeneratorfunction(fn):

            @functools.wraps(fn)
            def gen_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = trace.get_tracer(TRACER_NAME, __version__)
                with tracer.start_as_current_span(span_name) as span:
                    _set_input(span, args, kwargs)
                    try:
                        yield from fn(*args, **kwargs)
                    except Exception as exc:
                        _record_exception(span, exc)
                        raise

            return gen_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(TRACER_NAME, __version__)
            with tracer.start_as_current_span(span_name) as span:
                _set_input(span, args, kwargs)
                try:
                    result = fn(*args, **kwargs)
                except Exception as exc:
                    _record_exception(span, exc)
                    raise
                _set_output(span, result)
                return result

        return sync_wrapper

    if func is not None:
        return decorate(func)
    return decorate
