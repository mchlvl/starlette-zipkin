import asyncio
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, Union, cast
import aiozipkin as az
from aiozipkin.span import SpanAbc

from .middleware import get_root_span, get_tracer

_cur_span_ctx_var: ContextVar[Optional[SpanAbc]] = ContextVar(
    "current_span", default=None
)


def make_headers():
    child_span = _cur_span_ctx_var.get()
    return child_span.context.make_headers() if child_span else {}


class trace:
    """Decorator and context manager to handle trace easily."""

    def __init__(self, name: str, kind: str = az.SERVER) -> None:
        self._name = name
        self._kind = kind
        self._span: Optional[SpanAbc] = None

    @property
    def trace_id(self):
        return self._span.context.trace_id

    def __call__(self, func: Callable) -> Callable:

        if asyncio.iscoroutinefunction(cast(Any, func)):
            @wraps(func)
            async def inner_coro(*args: Any, **kwds: Any) -> Any:
                async with self:
                    return await func(*args, **kwds)

            return inner_coro
        else:
            @wraps(func)
            def inner(*args: Any, **kwds: Any) -> Any:
                with self:
                    return func(*args, **kwds)

            return inner

    def tag(self, key: str, value: str) -> "trace":
        """Add a tag to the current trace span."""
        if self._span is None:
            raise RuntimeError(f"{self} used outside the context manager")
        self._span.tag(key, value)
        return self

    def annotate(self, value: Optional[str], ts: Optional[float] = None) -> "trace":
        """Add an annotation to the current trace span."""
        if self._span is None:
            raise RuntimeError(f"{self} used outside the context manager")
        self._span.annotate(value, ts)
        return self

    def __enter__(self) -> "trace":
        tracer = get_tracer()
        parent = _cur_span_ctx_var.get()
        if parent is None:
            parent = get_root_span()
        self._span = tracer.new_child(parent.context)
        self._tok = _cur_span_ctx_var.set(self._span)
        parent = _cur_span_ctx_var.get()
        self._span.__enter__()
        self._span.name(self._name)
        self._span.kind(self._kind)
        return self

    def __exit__(self, *exc: Any) -> None:
        _cur_span_ctx_var.reset(self._tok)
        if self._span:
            self._span.__exit__(*exc)

    async def __aenter__(self) -> "trace":
        return self.__enter__()

    async def __aexit__(self, *exc: Any) -> None:
        return self.__exit__(*exc)
