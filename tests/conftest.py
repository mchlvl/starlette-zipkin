import pytest

import aiozipkin as az
from aiozipkin.transport import TransportABC

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette_zipkin import B3Headers, UberHeaders
from starlette_zipkin.trace import _tracer_ctx_var, install_root_span, reset_root_span


@pytest.fixture
def b3_keys():
    return B3Headers.KEYS


@pytest.fixture
def uber_keys():
    return UberHeaders.KEYS


@pytest.fixture
def app(tracer):
    app = Starlette()

    @app.route("/sync-message")
    def hi(request):
        return PlainTextResponse("ok")

    @app.route("/async-message")
    async def hi(request):
        return PlainTextResponse("ok")

    return app


class DummyTransport(TransportABC):
    def __init__(self) -> None:
        super().__init__()
        self.records = []

    def send(self, record) -> None:
        self.records.append(record.asdict())

    async def close(self) -> None:
        pass


@pytest.fixture
def transport():
    return DummyTransport()


@pytest.fixture
def tracer(transport):
    endpoint = az.create_endpoint("dummy-service")
    sampler = az.Sampler(sample_rate=1.0)
    tracer = az.Tracer(transport, sampler, endpoint)
    tok = _tracer_ctx_var.set(tracer)
    yield tracer
    _tracer_ctx_var.reset(tok)


@pytest.fixture
def root_span(tracer):
    span = tracer.new_trace()
    tok = install_root_span(span)
    yield span
    reset_root_span(tok)
