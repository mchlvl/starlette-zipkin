import logging
import os
import aiozipkin as az
import traceback
from typing import Any
from contextvars import ContextVar
from urllib.parse import urlunparse
from opentracing.ext import tags
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request


ZIPKIN_AGENT_HOST = os.getenv("ZIPKIN_AGENT_HOST", "localhost")
ZIPKIN_AGENT_PORT = int(os.getenv("ZIPKIN_AGENT_PORT", "9411"))
ZIPKIN_SERVICE_NAME = os.getenv("ZIPKIN_SERVICE_NAME", "service_name")
ZIPKIN_SAMPLING_RATE = float(os.getenv("ZIPKIN_SAMPLING_RATE", "1.0"))
ZIPKIN_SAMPLED = os.getenv("ZIPKIN_SAMPLED", "1") == "1"
ZIPKIN_ROOT_NAME = os.getenv("ZIPKIN_ROOT_NAME", "Request")

X_B3_TRACEID = "X-B3-TraceId"
ROOT_SPAN_CTX_KEY = "root_span"

_root_span_ctx_var: ContextVar[Any] = ContextVar(
    ROOT_SPAN_CTX_KEY, default=None
)


def get_root_span() -> str:
    return _root_span_ctx_var.get()


async def init_tracer(service_name=None):
    service_name = service_name or ZIPKIN_SERVICE_NAME
    endpoint = az.create_endpoint(service_name)
    tracer = await az.create(
        f"http://{ZIPKIN_AGENT_HOST}:{ZIPKIN_AGENT_PORT}/api/v2/spans",
        endpoint,
        sample_rate=ZIPKIN_SAMPLING_RATE,
    )
    return tracer


class ZipkinTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):

        tracer = await init_tracer()

        if self.has_trace_id(request):
            kw = {"context": self.get_trace_context(request)}
            function = tracer.new_child
        else:
            kw = {"sampled": ZIPKIN_SAMPLED}
            function = tracer.new_trace

        with function(**kw) as span:
            try:
                # set root span using context variable
                root_span = _root_span_ctx_var.set(span)

                self.before(span, request.scope)
                response = await call_next(request)
                self.after(span, response)

                return response

            except Exception as error:
                self.error(span, error)
                raise error from None

            finally:
                _root_span_ctx_var.reset(root_span)

        await tracer.close()

    def has_trace_id(self, request):
        if X_B3_TRACEID in request.headers:
            return True
        else:
            return False

    def get_trace_context(self, request):
        return az.make_context(request.headers)

    def before(self, span, scope):
        span.name(ZIPKIN_ROOT_NAME)
        span.tag(tags.SPAN_KIND, "root")
        span.tag(tags.COMPONENT, "asgi")
        span.tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)
        if scope["type"] in {"http", "websocket"}:
            span.tag(tags.HTTP_METHOD, scope["method"])
            span.tag(tags.HTTP_URL, self.get_url(scope))
            span.tag("http.route", scope["path"])
            span.tag("http.headers", self.get_headers(scope))

    def after(self, span, response):
        # if context header not filled in by other function,
        # add tracing info
        if X_B3_TRACEID not in response.headers:
            trace_headers = span.context.make_headers()
            logging.info(trace_headers)
            response.headers.update(trace_headers)
        span.tag("http.status_code", response.status_code)
        span.tag("http.response.headers", dict(response.headers))

    def error(self, span, error):
        span.tag("error", True)
        tb = traceback.format_exc()
        span.annotate(error)
        span.annotate(tb)

    def get_url(self, scope):
        host, port = scope["server"]
        url = urlunparse(
            (
                scope["scheme"],
                f"{host}:{port}",
                scope["path"],
                "",
                scope["query_string"],
                "",
            )
        )
        return url

    def get_headers(self, scope):
        headers = {}
        for raw_key, raw_value in scope["headers"]:
            key = raw_key.decode("latin-1")
            value = raw_value.decode("latin-1")
            if key in headers:
                headers[key] = headers[key] + ", " + value
            else:
                headers[key] = value
        return headers
