from abc import ABC, abstractmethod
from typing import List, Union

from aiozipkin.helpers import TraceContext
from aiozipkin.span import SpanAbc
from starlette.responses import Response


class Headers(ABC):
    TRACE_ID_HEADER: str = ""
    KEYS: List = []

    @abstractmethod
    def make_headers(self, context: TraceContext, response_headers: dict) -> dict:
        pass

    @abstractmethod
    def make_context(self, headers: dict) -> dict:
        pass

    @abstractmethod
    def get_trace_id(self, headers: dict) -> Union[str, None]:
        pass

    def update_headers(self, span: SpanAbc, response: Response) -> None:
        response_trace_id = self.get_trace_id(response.headers)

        trace_headers = self.make_headers(span.context, response.headers)

        # only update headers if headers not already set for this trace_id
        # ! need this check, since the default value is always context from
        # previous request
        if response_trace_id != span.context.trace_id:
            response.headers.update(trace_headers)
