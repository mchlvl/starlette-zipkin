"""
Patching GraphQLApp with prisma playground
"""
from starlette.graphql import GraphQLApp as BaseGraphQLApp
from starlette.responses import HTMLResponse
from starlette.concurrency import run_in_threadpool

from api.playground import PLAYGROUND

from typing import Any
from graphql.execution.executors.asyncio import AsyncioExecutor


class GraphQLApp(BaseGraphQLApp):
    def __init__(
        self,
        schema: "graphene.Schema",
        executor: Any = None,
        executor_class: type = None,
        graphiql: bool = True,
        middleware: list = [],
    ) -> None:
        self.schema = schema
        self.graphiql = graphiql
        if executor is None:
            self.executor = executor
            self.executor_class = executor_class
            self.is_async = executor_class is not None and issubclass(
                executor_class, AsyncioExecutor
            )
        self.middleware = middleware

    async def handle_graphiql(self, request):
        return HTMLResponse(PLAYGROUND)

    async def execute(
        self, query, variables=None, context=None, operation_name=None
    ):
        if self.is_async:
            return await self.schema.execute(
                query,
                variables=variables,
                operation_name=operation_name,
                executor=self.executor,
                return_promise=True,
                context=context,
                middleware=self.middleware,
            )
        else:
            return await run_in_threadpool(
                self.schema.execute,
                query,
                variables=variables,
                operation_name=operation_name,
                context=context,
                middleware=self.middleware,
            )
