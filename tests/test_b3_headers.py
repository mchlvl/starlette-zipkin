from starlette.testclient import TestClient
from starlette_zipkin import ZipkinMiddleware, ZipkinConfig, B3Headers as Headers


def test_sync(app, b3_keys):
    config = ZipkinConfig(header_formatter=Headers)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in b3_keys)


def test_async(app, b3_keys):
    config = ZipkinConfig(header_formatter=Headers)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in b3_keys)


def test_sync_request_data(app, b3_keys):
    config = ZipkinConfig(header_formatter=Headers)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in b3_keys)

    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in b3_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/sync-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert all(key in response2.headers for key in b3_keys)
    assert "x-b3-parentspanid" in response2.headers
    assert (
        headers[Headers.TRACE_ID_HEADER]
        == response2.headers[Headers.TRACE_ID_HEADER]
    )
    assert headers["x-b3-spanid"] == response2.headers["x-b3-parentspanid"]


def test_async_request_data(app, b3_keys):
    config = ZipkinConfig(header_formatter=Headers)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in b3_keys)

    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in b3_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/async-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert all(key in response2.headers for key in b3_keys)
    assert "x-b3-parentspanid" in response2.headers
    assert (
        headers[Headers.TRACE_ID_HEADER]
        == response2.headers[Headers.TRACE_ID_HEADER]
    )
    assert headers["x-b3-spanid"] == response2.headers["x-b3-parentspanid"]
