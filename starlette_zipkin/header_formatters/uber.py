"""
https://www.jaegertracing.io/docs/1.7/client-libraries/
https://github.com/aio-libs/aiozipkin/blob/v0.5.0/aiozipkin/helpers.py
"""
from aiozipkin.helpers import (
    TRACE_ID_HEADER,
    SPAN_ID_HEADER,
    PARENT_ID_HEADER,
    make_context,
    TraceContext,
)
from .template import Headers


class UberTraceId(Headers):
    TRACE_ID_HEADER = "uber-trace-id"

    def make_headers(self, context, response_headers):
        # if headers injected in b3 format, convert
        if TRACE_ID_HEADER in response_headers:
            context = self.make_context(response_headers)

        parent_span_id = (
            context.parent_id if context.parent_id is not None else "0"
        )

        if context.debug:
            flags = "2"
        elif context.sampled:
            flags = "1"
        else:
            flags = "0"

        headers = {
            self.TRACE_ID_HEADER: f"{context.trace_id}:{context.span_id}:{parent_span_id}:{flags}"
        }

        return headers

    def make_context(self, headers):
        has_uber = self.TRACE_ID_HEADER in headers

        if has_uber:
            trace_id, parent_id, span_id, debug, sampled = self._parse_uber_headers(
                headers
            )
            return TraceContext(
                trace_id=headers[TRACE_ID_HEADER.lower()],
                parent_id=headers.get(PARENT_ID_HEADER.lower()),
                span_id=headers[SPAN_ID_HEADER.lower()],
                sampled=sampled,
                debug=debug,
                shared=False,
            )
        else:
            return make_context(headers)

    def _parse_uber_headers(self, headers):
        trace_id, parent_id, span_id, flags = headers[
            self.TRACE_ID_HEADER
        ].split(":")
        debug = flags == "2"
        sampled = debug if debug else flags == "1"
        return trace_id, parent_id, span_id, debug, sampled
