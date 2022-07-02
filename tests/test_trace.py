import pytest

from starlette_zipkin import trace
from starlette_zipkin.trace import _cur_span_ctx_var


def test_trace_decorator_sync(transport, root_span):

    dummy_trace = None

    @trace("my dummy trace")
    def traced_function():
        nonlocal dummy_trace
        dummy_trace = _cur_span_ctx_var.get()

    traced_function()
    dummy_record = dummy_trace._record.asdict()
    assert dummy_record == {
        "annotations": [],
        "debug": False,
        "duration": dummy_record["duration"],
        "id": dummy_trace.context.span_id,
        "kind": "SERVER",
        "localEndpoint": {"serviceName": "dummy-service"},
        "name": "my dummy trace",
        "parentId": root_span.context.span_id,
        "remoteEndpoint": None,
        "shared": False,
        "tags": {},
        "timestamp": dummy_record["timestamp"],
        "traceId": root_span.context.trace_id,
    }
    assert transport.records == [dummy_record]


@pytest.mark.asyncio
async def test_trace_decorator_async(transport, root_span):

    dummy_trace = None

    @trace("my dummy trace")
    async def traced_function():
        nonlocal dummy_trace
        dummy_trace = _cur_span_ctx_var.get()

    await traced_function()
    dummy_record = dummy_trace._record.asdict()
    assert dummy_record == {
        "annotations": [],
        "debug": False,
        "duration": dummy_record["duration"],
        "id": dummy_trace.context.span_id,
        "kind": "SERVER",
        "localEndpoint": {"serviceName": "dummy-service"},
        "name": "my dummy trace",
        "parentId": root_span.context.span_id,
        "remoteEndpoint": None,
        "shared": False,
        "tags": {},
        "timestamp": dummy_record["timestamp"],
        "traceId": root_span.context.trace_id,
    }
    assert transport.records == [dummy_record]


def test_trace_context(transport, root_span):

    dummy_trace = None

    with trace("my dummy trace") as span:
        span.annotate("dummy annotation")
        dummy_trace = _cur_span_ctx_var.get()

    dummy_record = dummy_trace._record.asdict()
    assert dummy_record == {
        "annotations": [
            {
                "timestamp": dummy_record["annotations"][0]["timestamp"],
                "value": "dummy annotation",
            }
        ],
        "debug": False,
        "duration": dummy_record["duration"],
        "id": dummy_trace.context.span_id,
        "kind": "SERVER",
        "localEndpoint": {"serviceName": "dummy-service"},
        "name": "my dummy trace",
        "parentId": root_span.context.span_id,
        "remoteEndpoint": None,
        "shared": False,
        "tags": {},
        "timestamp": dummy_record["timestamp"],
        "traceId": root_span.context.trace_id,
    }
    assert transport.records == [dummy_record]


@pytest.mark.asyncio
async def test_trace_context_async(transport, root_span):

    dummy_trace = None

    async with trace("my dummy trace"):
        dummy_trace = _cur_span_ctx_var.get()

    dummy_record = dummy_trace._record.asdict()
    assert dummy_record == {
        "annotations": [],
        "debug": False,
        "duration": dummy_record["duration"],
        "id": dummy_trace.context.span_id,
        "kind": "SERVER",
        "localEndpoint": {"serviceName": "dummy-service"},
        "name": "my dummy trace",
        "parentId": root_span.context.span_id,
        "remoteEndpoint": None,
        "shared": False,
        "tags": {},
        "timestamp": dummy_record["timestamp"],
        "traceId": root_span.context.trace_id,
    }
    assert transport.records == [dummy_record]


@pytest.mark.asyncio
async def test_many_traces(transport, root_span):

    dummy_trace_1 = dummy_trace_2 = dummy_trace_3 = dummy_trace_4 = None

    @trace("my dummy trace 3")
    def traced_function():
        nonlocal dummy_trace_3, dummy_trace_4
        dummy_trace_3 = _cur_span_ctx_var.get()
        with trace("my dummy trace 4"):
            dummy_trace_4 = _cur_span_ctx_var.get()

    @trace("my dummy trace 1")
    async def async_traced_function():
        nonlocal dummy_trace_1, dummy_trace_2
        dummy_trace_1 = _cur_span_ctx_var.get()
        async with trace("my dummy trace 3"):
            dummy_trace_2 = _cur_span_ctx_var.get()
            traced_function()

    await async_traced_function()

    assert transport.records == [
        dummy_trace_4._record.asdict(),
        dummy_trace_3._record.asdict(),
        dummy_trace_2._record.asdict(),
        dummy_trace_1._record.asdict(),
    ]


def test_trace_id(root_span):
    with trace("my dummy trace 4") as child_span:
        assert child_span.trace_id is not None
        assert child_span.trace_id == root_span.context.trace_id


def test_headers(root_span):
    with trace("my dummy trace 4") as child_span:
        assert trace.make_headers() == {
            "X-B3-Flags": "0",
            "X-B3-ParentSpanId": root_span.context.span_id,
            "X-B3-Sampled": "1",
            "X-B3-SpanId": child_span._span.context.span_id,
            "X-B3-TraceId": child_span.trace_id,
        }


def test_trace_without_middleware():
    """Test the code passes through without the instrumenting middleware"""
    dummy_trace = None
    with trace("my dummy trace") as span:
        span.annotate("dummy annotation")
        span.tag("key", "value")
        trace_id = span.trace_id
        headers = span.make_headers()
        dummy_trace = _cur_span_ctx_var.get()
    assert dummy_trace is None
    assert trace_id is None
    assert headers == {}


@pytest.mark.asyncio
async def test_trace_without_middleware_async():
    """Test the code passes through without the instrumenting middleware"""
    dummy_trace = None
    async with trace("my dummy trace") as span:
        span.annotate("dummy annotation")
        span.tag("key", "value")
        trace_id = span.trace_id
        headers = span.make_headers()
        dummy_trace = _cur_span_ctx_var.get()
    assert dummy_trace is None
    assert trace_id is None
    assert headers == {}
