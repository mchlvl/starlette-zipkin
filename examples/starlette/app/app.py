import asyncio
import os
from random import random

import uvicorn
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette_zipkin import ZipkinConfig, ZipkinMiddleware, trace

TRACER = os.getenv("tracer", "zipkin")


@trace("api call", "CLIENT")
async def api_call():
    async with AsyncClient() as cli:
        return await cli.get("http://api:8000/", headers=trace.make_headers())


async def homepage(request):
    with trace("before api"):
        await asyncio.sleep(random())

    response = await api_call()

    with trace("after api", "PRODUCER"):
        await asyncio.sleep(random())

    return JSONResponse(response.json())


routes = [
    Route("/", homepage),
]

app = Starlette(debug=True, routes=routes)

config = ZipkinConfig(host=TRACER, service_name="app")
app.add_middleware(ZipkinMiddleware, config=config)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
