import asyncio
import os
import random

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette_zipkin import ZipkinConfig, ZipkinMiddleware, trace

TRACER = os.getenv("tracer", "zipkin")


async def homepage(request):

    with trace("awesome api sub trace") as child_span:
        # ! if headers not explicitly provided,\
        # root span from middleware injects headers
        # and becomes the parent for subsequet services
        wait = random.random()
        child_span.annotate(
            f"Child, sleeps for {wait}, injects headers and becomes parent"
        )
        await asyncio.sleep(wait)
        return JSONResponse({"trace_id": child_span.trace_id})


routes = [
    Route("/", homepage),
]

app = Starlette(debug=True, routes=routes)

config = ZipkinConfig(host=TRACER, service_name="api")
app.add_middleware(ZipkinMiddleware, config=config)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
