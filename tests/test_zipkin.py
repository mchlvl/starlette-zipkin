from starlette.testclient import TestClient
from zipkin_asgi import ZipkinMiddleware


def test_sync_request_data(app, x_b_keys):
    app.add_middleware(ZipkinMiddleware)
    client = TestClient(app)
    response = client.get("/sync-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in x_b_keys)

    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in x_b_keys:
        headers[key] = response.headers[key]
    response2 = client.get("/sync-message?foo=bar", headers=headers)
    assert response2.status_code == 200
    assert all(key in response2.headers for key in x_b_keys)
    assert "x-b3-parentspanid" in response2.headers
    assert headers["x-b3-traceid"] == response2.headers["x-b3-traceid"]
    assert headers["x-b3-spanid"] == response2.headers["x-b3-parentspanid"]


def test_async_request_data(app, x_b_keys):
    app.add_middleware(ZipkinMiddleware)
    client = TestClient(app)
    response = client.get("/async-message?foo=bar")
    assert response.status_code == 200
    assert all(key in response.headers for key in x_b_keys)

    # call with injected tracing headers - needs to follow up
    headers = {}
    for key in x_b_keys:
        headers[key] = response.headers[key]
    response = client.get("/async-message?foo=bar", headers=headers)
    assert response.status_code == 200
    assert all(key in response.headers for key in x_b_keys)
    assert "x-b3-parentspanid" in response.headers
    assert headers["x-b3-traceid"] == response.headers["x-b3-traceid"]
    assert headers["x-b3-spanid"] == response.headers["x-b3-parentspanid"]
