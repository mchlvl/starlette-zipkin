<p align="center"><em>AioZipkin middleware for Starlette/FastApi</em></p>
<p align="center">
<a href="https://github.com/mchlvl/starlette-zipkin/actions?query=workflow%3ACI" target="_blank">
    <img src="https://github.com/mchlvl/starlette-zipkin/workflows/CI/badge.svg" alt="Test">
</a>
<a href="https://codecov.io/gh/mchlvl/starlette-zipkin" target="_blank">
    <img src="https://img.shields.io/codecov/c/github/mchlvl/starlette-zipkin?color=%2334D058" alt="Coverage">

</a>
<a href="https://pypi.org/project/starlette-zipkin" target="_blank">
    <img src="https://img.shields.io/pypi/v/starlette-zipkin?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
</p>

## Features
- Using [sentry-asgi](https://github.com/encode/sentry-asgi) as a boilerplate
- Client - based on `aiozipkin` - async compatible zipkin library
- Server (any zipkin 2.0 compatible server will work) - Jaeger examples
- Middleware tracing http traffic
- Injecting tracing headers to responses
- Extracting tracing headers from requests
- Context variable with the span for every incoming request - possible to instrument tracing of lower level operations

## Quick start

### Run tracing server


#### Jaeger all-in-one

Follow instructions at [https://www.jaegertracing.io/docs/latest/getting-started/](https://www.jaegertracing.io/docs/latest/getting-started/)

```
$ docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

Trace queries at [http://localhost:16686/](http://localhost:16686/)


### Add middleware

```
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from starlette_zipkin import ZipkinMiddleware

routes = [
    Route("/", JSONResponse({"status": "OK"})),
]

app = Starlette(debug=True, routes=routes)

app.add_middleware(ZipkinMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=True)
```

By default the client emits to `http://localhost:9411`.

All traffic is captured and available at [http://localhost:16686/](http://localhost:16686/)

## Advanced Tutorial

To instrument tracing at lower levels, two helper functions are available:

- `get_root_span` - returns the span instance corresponding to current request
- `get_tracer` - returns the tracer instance corresponding to current request
- `trace` - create span in the trace

```
import json
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from starlette_zipkin import (
    ZipkinMiddleware,
    ZipkinConfig,
    trace,
    B3Headers,
    UberHeaders
)


async def homepage(request):

    with trace("NewParent") as child_span:
        # ! if headers not explicitly provided,\
        # root span from middleware injects headers
        # and becomes the parent for subsequet services
        headers = child_span.context.make_headers()
        child_span.kind("SERVER")
        # possible span kinds
        # CLIENT = "CLIENT"
        # SERVER = "SERVER"
        # PRODUCER = "PRODUCER"
        # CONSUMER = "CONSUMER"
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
    sample_rate=1.0,
    inject_response_headers=True,
    force_new_trace=False,
    json_encoder=json.dumps,
    header_formatter=B3Headers
)
app.add_middleware(ZipkinMiddleware, config=config)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=True)
```

This way we are able to followup at the call from a different service. Here we use the same server, but pass the tracing headers to subsequent calls to demonstrate future spans:

## Configuration

To change the middleware configuration, provide a config object (here with default values being as shown)

```
import json
from starlette_zipkin import ZipkinMiddleware, ZipkinConfig, B3Headers

config = ZipkinConfig(
    host="localhost",
    port=9411,
    service_name="service_name",
    sample_rate=1.0,
    inject_response_headers=True,
    force_new_trace=False,
    json_encoder=json.dumps,
    header_formatter=B3Headers
)

app = Starlette()

app.add_middleware(ZipkinMiddleware, config=config)
```

where:

- `host = "localhost"`
    - default local host, needs to be set to point at the agent that collects traces (e.g. jaeger-agent)
- `port = 9411`
    - default port, needs to be set to point at the agent that collects traces (e.g. jaeger-agent)
    - 9411 is default for zipkin client/agent (and jaeger-agent)
    - make sure to make accessible
- `service_name = "service_name"`
    - name of the service
- `sample_rate = 1.0`
    - zipkin sampling rate, default samples every call
- `inject_response_headers = True`
    - automatically inject response headers
- `force_new_trace = False`
    - if `True`, does not create child traces if incoming request contains tracing headers
- `json_encoder=json.dumps`
    - json encoder can be provided, defaults to json dumps. It is used to format dictionaries for Jaeger UI.
- `header_formatter=B3Headers`
    - defaults to b3 headers format. Can be switched to UberHeaders, which imply the `uber-trace-id` format.