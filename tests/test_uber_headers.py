import pytest
from starlette.testclient import TestClient
from starlette_zipkin import (
    ZipkinMiddleware,
    ZipkinConfig,
    UberHeaders as Headers,
)


def test_sync(app, tracer, uber_keys):
    config = ZipkinConfig(header_formatter=Headers)
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in uber_keys)


def test_async(app, tracer, uber_keys):
    config = ZipkinConfig(header_formatter=Headers)
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in uber_keys)


def test_sync_request_data(app, tracer, uber_keys):
    config = ZipkinConfig(header_formatter=Headers)
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in uber_keys)
    trace_id, span_id, parent_id, debug, sampled = Headers()._parse_uber_headers(
        response.headers
    )

    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in uber_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/sync-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert all(key in response2.headers for key in uber_keys)

    trace_id2, span_id2, parent_id2, debug2, sampled2 = Headers()._parse_uber_headers(
        response2.headers
    )
    assert trace_id == trace_id2
    assert span_id == parent_id2


def test_async_request_data(app, tracer, uber_keys):
    config = ZipkinConfig(header_formatter=Headers)
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in uber_keys)
    trace_id, span_id, parent_id, debug, sampled = Headers()._parse_uber_headers(
        response.headers
    )

    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in uber_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/async-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert all(key in response2.headers for key in uber_keys)

    trace_id2, span_id2, parent_id2, debug2, sampled2 = Headers()._parse_uber_headers(
        response2.headers
    )
    assert trace_id == trace_id2
    assert span_id == parent_id2


@pytest.mark.parametrize("split_char", [(":"), ("%3A")])
def test_split_char(app, tracer, uber_keys, split_char):
    config = ZipkinConfig(header_formatter=Headers, header_formatter_kwargs=dict(split_char=split_char))
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in uber_keys)
    item = response.headers.get('uber-trace-id')
    assert split_char in item
