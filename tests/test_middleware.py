import pytest

from starlette_zipkin import ZipkinConfig, ZipkinMiddleware, middleware


@pytest.mark.asyncio
async def test_dispatch_trace_new_child(app, dummy_request, next_response):
    trace_id = "6223635aa7bfb6597d72ac7c4680bfed"
    span_id = "ac7cb16943218de4"
    config = ZipkinConfig("zipkin.host")
    middleware = ZipkinMiddleware(app, config=config)
    # the tracer is initialized on the first dispatch
    assert middleware.tracer is None
    resp = await middleware.dispatch(
        dummy_request(
            headers={
                "x-b3-spanid": span_id,
                "x-b3-traceid": trace_id,
            }
        ),
        next_response,
    )
    assert middleware.tracer is not None
    assert middleware.tracer._transport is not None
    assert str(middleware.tracer._transport._address) == "http://zipkin.host:9411/api/v2/spans"
    assert resp.headers["x-b3-spanid"] == span_id
    assert resp.headers["x-b3-traceid"] == trace_id
    await middleware.tracer.close()


@pytest.mark.asyncio
async def test_dispatch_trace(app, dummy_request, next_response):
    config = ZipkinConfig()
    middleware = ZipkinMiddleware(app, config=config)
    # the tracer is initialized on the first dispatch
    assert middleware.tracer is None
    resp = await middleware.dispatch(
        dummy_request(headers={}),
        next_response,
    )
    assert middleware.tracer is not None
    assert middleware.tracer._transport is not None
    assert str(middleware.tracer._transport._address) == "http://localhost:9411/api/v2/spans"
    assert resp.headers["x-b3-flags"] == "0"
    assert resp.headers["x-b3-sampled"] == "1"
    assert resp.headers["x-b3-spanid"] == resp.headers["x-b3-spanid"]
    assert resp.headers["x-b3-traceid"] == resp.headers["x-b3-traceid"]
    await middleware.tracer.close()


@pytest.mark.asyncio
async def test_dispatch_trace_buggy_headers(app, dummy_request, next_response):
    trace_id = "6223635aa7bfb6597d72ac7c4680bfed"
    config = ZipkinConfig()
    middleware = ZipkinMiddleware(app, config=config)
    # the tracer is initialized on the first dispatch
    assert middleware.tracer is None
    resp = await middleware.dispatch(
        dummy_request(
            headers={
                "x-b3-traceid": trace_id,
                # x-b3-spanid should be here
            }
        ),
        next_response,
    )
    assert middleware.tracer is not None
    assert middleware.tracer._transport is not None
    assert resp.headers["x-b3-flags"] == "0"
    assert resp.headers["x-b3-sampled"] == "1"
    assert resp.headers["x-b3-spanid"] == resp.headers["x-b3-spanid"]
    assert resp.headers["x-b3-traceid"] == resp.headers["x-b3-traceid"]
    # we cannot reuse the traceid if the span id was missing
    assert trace_id != resp.headers["x-b3-spanid"]
    await middleware.tracer.close()


@pytest.mark.asyncio
async def test_dispatch_trace_reuse_tracer(app, dummy_request, next_response):
    config = ZipkinConfig()
    middleware = ZipkinMiddleware(app, config=config)
    # the tracer is initialized on the first dispatch
    assert middleware.tracer is None
    await middleware.dispatch(dummy_request(), next_response)
    assert middleware.tracer is not None
    tracer = middleware.tracer
    await middleware.dispatch(dummy_request(), next_response)
    assert middleware.tracer is tracer, "Tracer must be reused on every requests"
    await tracer.close()


@pytest.mark.parametrize(
    "params",
    [
        {"headers": [(b"a", b"A, B")]},
        {"headers": [(b"a", b"A"), (b"a", b"B")]},
    ],
)
def test_get_headers(app, params):
    config = ZipkinConfig()
    middleware = ZipkinMiddleware(app, config=config)
    headers = middleware.get_headers({"headers": params["headers"]})
    assert headers == '{"a": "A, B"}'


@pytest.mark.parametrize(
    "params",
    [
        {
            "querystring": b"",
            "expected": "",
        },
        {
            "querystring": b"a=A&b=B",
            "expected": "a=A&b=B",
        },
        {
            "querystring": b"a=A&a=a",
            "expected": "a=A&a=a",
        },
        {
            "querystring": b"a=A%20a",
            "expected": "a=A a",
        },
    ],
)
def test_get_query(app, params):
    config = ZipkinConfig()
    middleware = ZipkinMiddleware(app, config=config)
    querystring = middleware.get_query({"query_string": params["querystring"]})
    assert querystring == params["expected"]


class DummyEndpoint:
    def __init__(self, qualname, name):
        self.__qualname__ = qualname
        self.__name__ = name


@pytest.mark.parametrize(
    "params",
    [
        {
            "endpoint": "",
            "expected": "",
        },
        {
            "endpoint": DummyEndpoint("qualname", "name"),
            "expected": "test_middleware.qualname",
        },
        {
            "endpoint": DummyEndpoint(None, "name"),
            "expected": "test_middleware.name",
        },
    ],
)
def test_get_transaction(app, params):
    config = ZipkinConfig()
    middleware = ZipkinMiddleware(app, config=config)
    transac = middleware.get_transaction({"endpoint": params["endpoint"]})
    assert transac == params["expected"]


def test_get_ip_with_hostname_that_resolves(monkeypatch):
    monkeypatch.setattr(middleware.socket, "gethostname", lambda: "localhost")
    assert middleware.get_ip() == "127.0.0.1"


def test_get_ip_without_hostname_that_resolves(monkeypatch):
    monkeypatch.setattr(middleware.socket, "gethostname", lambda: "thishostnamewontresolve")
    assert middleware.get_ip() == "0.0.0.0"
