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


ROOT_SPAN_CTX_KEY = "root_span"
ZIPKIN_SERVICE_NAME_CTX_KEY = "zipkin_config"
X_B3_TRACEID = "X-B3-TraceId"


_root_span_ctx_var: ContextVar[Any] = ContextVar(
    ROOT_SPAN_CTX_KEY, default=None
)
_zipkin_config_ctx_var: ContextVar[Any] = ContextVar(
    ZIPKIN_SERVICE_NAME_CTX_KEY, default=None
)


class ZipkinConfig:
    def __init__(
        self,
        host="localhost",
        port=9411,
        service_name="service_name",
        sampling_rate=1.0,
        sampled=True,
        root_span_name="Request",
        inject_response_headers=True,
        force_new_trace=False,
    ):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.sampling_rate = sampling_rate
        self.sampled = sampled
        self.root_span_name = root_span_name
        self.inject_response_headers = inject_response_headers
        self.force_new_trace = force_new_trace


class ZipkinMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, dispatch=None, config=None):
        self.app = app
        self.dispatch_func = self.dispatch if dispatch is None else dispatch
        self.config = config or ZipkinConfig()
        _zipkin_config_ctx_var.set(self.config)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):

        tracer = await init_tracer()

        if self.has_trace_id(request) and not self.config.force_new_trace:
            kw = {"context": self.get_trace_context(request)}
            function = tracer.new_child
        else:
            kw = {"sampled": self.config.sampled}
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
        span.name(self.config.root_span_name)
        span.tag(tags.SPAN_KIND, "root")
        span.tag(tags.COMPONENT, "asgi")
        span.tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)
        if scope["type"] in {"http", "websocket"}:
            span.tag(tags.HTTP_METHOD, scope["method"])
            span.tag(tags.HTTP_URL, self.get_url(scope))
            span.tag("http.route", scope["path"])
            span.tag("http.headers", self.get_headers(scope))
            span.tag("query_string", self.get_query(scope))
            # TODO: get body (need to check starlette if allows,
            # in experimental testing calls hang forever, if body
            # awaited before calling next)
        if scope.get("client"):
            span.tag("remote_address", scope["client"][0])
        if scope.get("endpoint"):
            span.tag("transaction", self.get_transaction(scope))

    def after(self, span, response):
        # if context header not filled in by other function,
        # add tracing info. Only if not surpressed by env
        if (
            X_B3_TRACEID not in response.headers
            and self.config.inject_response_headers
        ):
            trace_headers = span.context.make_headers()
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
                str(scope["query_string"]),
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
        return headers

    def get_query(self, scope):
        """
        Extract querystring from the ASGI scope, in the format that the Sentry protocol expects.
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


async def init_tracer():
    endpoint = az.create_endpoint(get_config_value("service_name"))
    tracer = await az.create(
        f"http://{get_config_value('host')}:{get_config_value('port')}/api/v2/spans",
        endpoint,
        sample_rate=get_config_value("sampling_rate"),
    )
    return tracer


def get_root_span() -> str:
    return _root_span_ctx_var.get()


def get_config_value(value: str) -> str:
    return getattr(_zipkin_config_ctx_var.get(), value)
