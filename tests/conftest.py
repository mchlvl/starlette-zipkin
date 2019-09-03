import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette_zipkin import B3Headers, UberHeaders


@pytest.fixture
def b3_keys():
    return B3Headers.KEYS


@pytest.fixture
def uber_keys():
    return UberHeaders.KEYS


@pytest.fixture
def app():
    app = Starlette()

    @app.route("/sync-message")
    def hi(request):
        return PlainTextResponse("ok")

    @app.route("/async-message")
    async def hi(request):
        return PlainTextResponse("ok")

    return app
