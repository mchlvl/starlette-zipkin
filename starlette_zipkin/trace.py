import asyncio
from contextvars import ContextVar
from functools import wraps
from typing import Optional

import aiozipkin as az
from aiozipkin.span import SpanAbc

from .middleware import get_root_span, get_tracer

_cur_span_ctx_var: ContextVar[Optional[SpanAbc]] = ContextVar(
    "current_span", default=None
)


class trace:
    """Decorator and context manager to handle trace easily."""

    def __init__(self, name, kind=az.SERVER) -> None:
        self._name = name
        self._kind = kind
        self._span = None

    def __call__(self, func):

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def inner(*args, **kwds):
                async with self:
                    return await func(*args, **kwds)

        else:

            def inner(*args, **kwds):
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

    def __enter__(self):
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

    def __exit__(self, *exc):
        _cur_span_ctx_var.reset(self._tok)
        self._span.__exit__(*exc)

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, *exc):
        return self.__exit__(*exc)
