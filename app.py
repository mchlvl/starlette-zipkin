import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from graphql.execution.executors.asyncio import AsyncioExecutor

from api.settings import GRAPHQL_ROUTE, DEBUG
from api.schema import schema
from api.graphqlapp import GraphQLApp
from api.middlewares.graphene import GrapheneZipkinMiddleware
from api.middlewares.zipkin import ZipkinMiddleware


routes = [
    Route("/", JSONResponse({"status": "OK"})),
    Route(
        GRAPHQL_ROUTE,
        GraphQLApp(
            schema=schema,
            executor_class=AsyncioExecutor,
            middleware=[GrapheneZipkinMiddleware()],
        ),
    ),
]

app = Starlette(debug=DEBUG, routes=routes)

app.add_middleware(ZipkinMiddleware)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=DEBUG)
