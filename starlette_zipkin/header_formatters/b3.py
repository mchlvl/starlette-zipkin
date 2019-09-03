from aiozipkin import make_context
from aiozipkin.helpers import make_headers, TRACE_ID_HEADER

from .template import Headers


class B3Headers(Headers):
    TRACE_ID_HEADER = TRACE_ID_HEADER

    @staticmethod
    def make_headers(context, response_headers):
        print("INNER", context, response_headers)
        # # inject headers, unless already provided
        # if TRACE_ID_HEADER not in response_headers:
        #     return make_headers(context)
        # else:
        #     return response_headers
        return context.make_headers()

    @staticmethod
    def make_context(headers):
        return make_context(headers)
