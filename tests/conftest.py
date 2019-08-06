import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse


@pytest.fixture
def x_b_keys():
    return ["x-b3-traceid", "x-b3-spanid", "x-b3-flags", "x-b3-sampled"]


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
