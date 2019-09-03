from abc import ABC, abstractmethod


class Headers(ABC):
    @abstractmethod
    def make_headers(self, context, response_headers):
        pass

    @abstractmethod
    def make_context(self):
        pass
