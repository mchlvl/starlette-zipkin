import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from zipkin_asgi import (
    ZipkinMiddleware,
    get_root_span,
    init_tracer,
)


async def homepage(request):
    root_span = get_root_span()
    tracer = await init_tracer()
    await asyncio.sleep(1)

    with tracer.new_child(root_span.context) as child_span:
        child_span.name("NewParent")
        child_span.tag("component", "second")
        child_span.annotate(
            "Child, sleeps for 1, injects headers and becomes parent"
        )
        await asyncio.sleep(1)

        # ! if headers not explicitly provided,\
        # root span from middleware injects headers
        # and becomes the x-b3-spanid unde which new span is traced
        headers = child_span.context.make_headers()
        return JSONResponse({"hello": "world"}, headers=headers)


routes = [
    Route("/", JSONResponse({"status": "OK"})),
    Route("/homepage", homepage),
]

app = Starlette(debug=True, routes=routes)

app.add_middleware(ZipkinMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=True)
