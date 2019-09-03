from abc import ABC, abstractmethod


class Headers(ABC):
    TRACE_ID_HEADER = ""
    KEYS = []

    @abstractmethod
    def make_headers(self, context, response_headers):
        pass

    @abstractmethod
    def make_context(self):
        pass

    @abstractmethod
    def get_trace_id(self, headers):
        pass

    def update_headers(self, span, response):
        response_trace_id = self.get_trace_id(response.headers)

        trace_headers = self.make_headers(span.context, response.headers)

        # only update headers if headers not already set for this trace_id
        # ! need this check, since the default value is always context from
        # previous request
        if response_trace_id != span.context.trace_id:
            response.headers.update(trace_headers)
