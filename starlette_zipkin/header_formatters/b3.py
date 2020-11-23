from typing import Union

from aiozipkin import make_context
from aiozipkin.helpers import (
    FLAGS_HEADER,
    SAMPLED_ID_HEADER,
    SPAN_ID_HEADER,
    TRACE_ID_HEADER,
    TraceContext,
)

from .template import Headers


class B3Headers(Headers):
    TRACE_ID_HEADER = TRACE_ID_HEADER.lower()
    KEYS = [
        TRACE_ID_HEADER.lower(),
        SPAN_ID_HEADER.lower(),
        SAMPLED_ID_HEADER.lower(),
        FLAGS_HEADER.lower(),
    ]

    def make_headers(self, context: TraceContext, response_headers: dict) -> dict:
        return context.make_headers()

    def make_context(self, headers: dict) -> dict:
        return make_context(headers)

    def get_trace_id(self, headers: dict) -> Union[str, None]:
        return headers.get(self.TRACE_ID_HEADER)
