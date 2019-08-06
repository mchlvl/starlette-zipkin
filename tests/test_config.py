from starlette.testclient import TestClient
from zipkin_asgi import ZipkinMiddleware, ZipkinConfig


def test_sync_no_inject(app, x_b_keys):
    config = ZipkinConfig(inject_response_headers=False)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert not any(key in response.headers for key in x_b_keys)


def test_async_no_inject(app, x_b_keys):
    config = ZipkinConfig(inject_response_headers=False)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    assert not any(key in response.headers for key in x_b_keys)


def test_sync_force_new_trace(app, x_b_keys):
    config = ZipkinConfig(force_new_trace=True)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in x_b_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/sync-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert "x-b3-parentspanid" not in response2.headers
    assert headers["x-b3-traceid"] != response2.headers["x-b3-traceid"]


def test_async_force_new_trace(app, x_b_keys):
    config = ZipkinConfig(force_new_trace=True)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in x_b_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/async-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert "x-b3-parentspanid" not in response2.headers
    assert headers["x-b3-traceid"] != response2.headers["x-b3-traceid"]


def test_sync_sampled(app, x_b_keys):
    config = ZipkinConfig(sampled=False)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert response.headers["x-b3-sampled"] == "0"


def test_async_sampled(app, x_b_keys):
    config = ZipkinConfig(sampled=False)
    app.add_middleware(ZipkinMiddleware, config=config)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    print(response.headers)
    assert response.status_code == 200
    assert response.headers["x-b3-sampled"] == "0"
