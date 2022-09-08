import pytest
from starlette.testclient import TestClient

from starlette_zipkin import ZipkinConfig, ZipkinMiddleware


def test_config_instance(app, tracer):
    with pytest.raises(ValueError):
        app.add_middleware(ZipkinMiddleware, config=TestClient, _tracer=tracer)


def test_sync_no_inject(app, tracer, b3_keys):
    config = ZipkinConfig(inject_response_headers=False)
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert not any(key in response.headers for key in b3_keys)


def test_async_no_inject(app, tracer, b3_keys):
    config = ZipkinConfig(inject_response_headers=False)
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    assert not any(key in response.headers for key in b3_keys)


def test_sync_force_new_trace(app, tracer, b3_keys):
    config = ZipkinConfig(force_new_trace=True)
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in b3_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/sync-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert "x-b3-parentspanid" not in response2.headers
    assert headers["x-b3-traceid"] != response2.headers["x-b3-traceid"]


def test_async_force_new_trace(app, tracer, b3_keys):
    config = ZipkinConfig(force_new_trace=True)
    app.add_middleware(ZipkinMiddleware, config=config, _tracer=tracer)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in b3_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/async-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert "x-b3-parentspanid" not in response2.headers
    assert headers["x-b3-traceid"] != response2.headers["x-b3-traceid"]
