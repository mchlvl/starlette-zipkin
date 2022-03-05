import pytest

from starlette_zipkin import ZipkinConfig, ZipkinMiddleware


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
    assert (
        str(middleware.tracer._transport._address)
        == "http://zipkin.host:9411/api/v2/spans"
    )
    assert dict(resp.headers) == {
        "x-b3-spanid": span_id,
        "x-b3-traceid": trace_id,
    }
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
    assert (
        str(middleware.tracer._transport._address)
        == "http://localhost:9411/api/v2/spans"
    )
    assert dict(resp.headers) == {
        "x-b3-flags": "0",
        "x-b3-sampled": "1",
        "x-b3-spanid": resp.headers["x-b3-spanid"],
        "x-b3-traceid": resp.headers["x-b3-traceid"],
    }
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
    assert dict(resp.headers) == {
        "x-b3-flags": "0",
        "x-b3-sampled": "1",
        "x-b3-spanid": resp.headers["x-b3-spanid"],
        "x-b3-traceid": resp.headers["x-b3-traceid"],
    }
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
