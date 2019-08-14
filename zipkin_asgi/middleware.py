import json
import aiozipkin as az
import traceback
import urllib
from typing import Any
from contextvars import ContextVar
from urllib.parse import urlunparse
from opentracing.ext import tags
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request


X_B3_TRACEID = "X-B3-TraceId"


_root_span_ctx_var: ContextVar[Any] = ContextVar("root_span", default=None)
_tracer_ctx_var: ContextVar[Any] = ContextVar("tracer", default=None)


class ZipkinConfig:
    def __init__(
        self,
        host="localhost",
        port=9411,
        service_name="service_name",
        sampling_rate=1.0,
        inject_response_headers=True,
        force_new_trace=False,
        json_encoder=json.dumps,
    ):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.sampling_rate = sampling_rate
        self.inject_response_headers = inject_response_headers
        self.force_new_trace = force_new_trace
        self.json_encoder = json_encoder


class ZipkinMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, dispatch=None, config=None):
        self.app = app
        self.dispatch_func = self.dispatch if dispatch is None else dispatch
        self.config = config or ZipkinConfig()
        self.validate_config()
        self.tracer = None

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):

        await self.init_tracer()
        tracer = get_tracer()

        if self.has_trace_id(request) and not self.config.force_new_trace:
            kw = {"context": az.make_context(request.headers)}
            function = tracer.new_child
        else:
            kw = {}
            function = tracer.new_trace

        with function(**kw) as span:
            try:
                # set root span using context variable
                root_span = _root_span_ctx_var.set(span)

                self.before(span, request.scope)
                response = await call_next(request)
                self.after(span, response)
                # getting body after request was evaluated due to:
                # https://github.com/encode/starlette/issues/495
                body = await request.body()
                if body:
                    span.tag(
                        "http.body",
                        self.config.json_encoder(await request.json()),
                    )
                return response

            except Exception as error:
                self.error(span, error)
                raise error from None

            finally:
                _root_span_ctx_var.reset(root_span)

        await tracer.close()

    async def init_tracer(self):
        endpoint = az.create_endpoint(self.config.service_name)
        tracer = await az.create(
            f"http://{self.config.host}:{self.config.port}/api/v2/spans",
            endpoint,
            sample_rate=self.config.sampling_rate,
        )
        self.tracer = tracer
        _tracer_ctx_var.set(tracer)

    def validate_config(self):
        if not isinstance(self.config, ZipkinConfig):
            raise ValueError("Config needs to be ZipkinConfig instance")

    def has_trace_id(self, request):
        # TODO: uber-id conversion
        if X_B3_TRACEID in request.headers:
            return True
        else:
            return False

    def before(self, span, scope):
        name = f'{scope["scheme"].upper()} {scope["method"]} {scope["path"]}'
        span.name(name)
        span.tag(tags.SPAN_KIND, "root")
        span.tag(tags.COMPONENT, "asgi")
        span.tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)
        if scope["type"] in {"http", "websocket"}:
            span.tag(tags.HTTP_METHOD, scope["method"])
            span.tag(tags.HTTP_URL, self.get_url(scope))
            span.tag("http.route", scope["path"])
            span.tag("http.headers", self.get_headers(scope))
        query = self.get_query(scope)
        if query:
            span.tag("query", query)
        if scope.get("client"):
            span.tag("remote_address", scope["client"][0])
        if scope.get("endpoint"):
            span.tag("transaction", self.get_transaction(scope))

    def after(self, span, response):
        """
        If context header not filled in by other function,
        add tracing info.
        """
        if (
            X_B3_TRACEID not in response.headers
            and self.config.inject_response_headers
        ):
            trace_headers = span.context.make_headers()
            response.headers.update(trace_headers)
        span.tag("http.status_code", response.status_code)
        span.tag(
            "http.response.headers",
            self.config.json_encoder(dict(response.headers)),
        )

    def error(self, span, error):
        span.tag("error", True)
        span.tag("error.object", type(error).__name__)
        span.tag("stack", traceback.format_exc())

    def get_url(self, scope):
        host, port = scope["server"]
        url = urlunparse(
            (
                scope["scheme"],
                f"{host}:{port}",
                scope["path"],
                "",
                scope["query_string"].decode("utf-8"),
                "",
            )
        )
        return url

    def get_headers(self, scope):
        """
        Extract headers from the ASGI scope.
        """
        headers = {}
        for raw_key, raw_value in scope["headers"]:
            key = raw_key.decode("latin-1")
            value = raw_value.decode("latin-1")
            if key in headers:
                headers[key] = headers[key] + ", " + value
            else:
                headers[key] = value
        return self.config.json_encoder(headers)

    def get_query(self, scope):
        """
        Extract querystring from the ASGI scope.
        """
        return urllib.parse.unquote(scope["query_string"].decode("latin-1"))

    def get_transaction(self, scope):
        """
        Return a transaction string to identify the routed endpoint.
        """
        endpoint = scope["endpoint"]
        qualname = (
            getattr(endpoint, "__qualname__", None)
            or getattr(endpoint, "__name__", None)
            or None
        )
        if not qualname:
            return None
        return "%s.%s" % (endpoint.__module__, qualname)


def get_root_span() -> str:
    return _root_span_ctx_var.get()


def get_tracer() -> str:
    return _tracer_ctx_var.get()
