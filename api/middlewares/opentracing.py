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
from graphql import GraphQLError

from api.settings import GRAPHQL_ROUTE
from api.settings import JAEGER_HOST, JAEGER_PORT, JAEGER_SERVICE_NAME
from api.utils import get_fields


ROOT_SPAN_CTX_KEY = "root_span"

_root_span_ctx_var: ContextVar[Any] = ContextVar(
    ROOT_SPAN_CTX_KEY, default=None
)


def get_root_span() -> str:
    return _root_span_ctx_var.get()


async def init_tracer(service_name=JAEGER_SERVICE_NAME):
    endpoint = az.create_endpoint(service_name)
    tracer = await az.create(
        f"http://{JAEGER_HOST}:{JAEGER_PORT}/api/v2/spans",
        endpoint,
        sample_rate=1.0,
    )
    return tracer


class OpenTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        tracer = await init_tracer()

        with tracer.new_trace(sampled=True) as span:
            try:
                # set root span using context variable
                root_span = _root_span_ctx_var.set(span)

                # set tags before calling next
                self.before(span, request.scope)

                # call next
                response = await call_next(request)

                # set tags & pass response headers
                self.after(span, response)
                return response
            except Exception as error:
                self.error(span, error)
                raise error from None
            finally:
                _root_span_ctx_var.reset(root_span)
        await tracer.close()

    def before(self, span, scope):
        name = "GraphQL" if scope["path"] == GRAPHQL_ROUTE else "Request"
        span.name(name)
        span.tag(tags.SPAN_KIND, "root")
        span.tag(tags.COMPONENT, "asgi")
        span.tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)
        if scope["type"] in {"http", "websocket"}:
            span.tag(tags.HTTP_METHOD, scope["method"])
            span.tag(tags.HTTP_URL, self.get_url(scope))
            span.tag("http.route", scope["path"])
            span.tag("http.headers", self.get_headers(scope))

    def after(self, span, response):
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


class GrapheneOpenTracing(object):
    async def resolve(self, next, root, info, **kwargs):

        if self.should_not_trace(info):
            return next(root, info, **kwargs)
        else:
            # ever resolver is child of the root (GraphQL)
            root_span = get_root_span()
            tracer = await init_tracer()
            with tracer.new_child(root_span.context) as span:
                span.name(info.field_name)
                span.tag("graphql.fields", get_fields(info))
                span.tag("component", "graphql")
                span.tag("graphql.parentType", info.parent_type.name)
                span.tag("graphql.path", info.path)
                if kwargs:
                    for kwarg, value in kwargs.items():
                        span.tag(f"graphql.param.{kwarg}", value)

                def on_error(error):
                    span.tag("error", True)
                    tb = traceback.format_exc()
                    span.annotate(error)
                    span.annotate(tb)
                    raise GraphQLError(error)

                # hijack the context to pass current span to resolvers
                info.context.update({"span": span})
                result = await next(root, info, **kwargs).catch(on_error)
                return result

    def should_not_trace(self, info):
        if (
            info.field_name not in info.parent_type.fields
            or "__schema" in info.path
        ):
            return True
        else:
            return False


async def trace_aiohttp_response(response, span, body=None):
    # aiohttp additional tracing parameters
    span.tag("http.url", response.url)
    span.tag("http.response.headers", dict(response.headers))
    span.tag("http.status_code", response.status)
    span.tag("http.method", response.method)
    span.tag("http.headers", dict(response.request_info.headers))
    if body:
        span.tag("http.body", body)
