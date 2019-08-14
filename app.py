import json
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from starlette_zipkin import (
    ZipkinMiddleware,
    ZipkinConfig,
    get_root_span,
    get_tracer,
)


async def homepage(request):
    root_span = get_root_span()
    tracer = get_tracer()

    with tracer.new_child(root_span.context) as child_span:
        # ! if headers not explicitly provided,\
        # root span from middleware injects headers
        # and becomes the parent for subsequet services
        headers = child_span.context.make_headers()
        child_span.name("NewParent")
        child_span.annotate(
            "Child, sleeps for 1, injects headers and becomes parent"
        )
        await asyncio.sleep(1)
        return JSONResponse({"hello": "world"}, headers=headers)


routes = [
    Route("/", JSONResponse({"status": "OK"})),
    Route("/homepage", homepage),
]

app = Starlette(debug=True, routes=routes)

config = ZipkinConfig(
    host="localhost",
    port=9411,
    service_name="service_name",
    sampling_rate=1.0,
    inject_response_headers=True,
    force_new_trace=False,
    json_encoder=json.dumps,
)
app.add_middleware(ZipkinMiddleware, config=config)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=True)
