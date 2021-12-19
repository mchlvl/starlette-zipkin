import json
from typing import Any, Callable

from .header_formatters import B3Headers


class ZipkinConfig:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9411,
        service_name: str = "service_name",
        sample_rate: float = 1.0,
        inject_response_headers: bool = True,
        force_new_trace: bool = False,
        json_encoder: Callable = json.dumps,
        header_formatter: Any = B3Headers,
        header_formatter_kwargs: dict = {},
    ):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.sample_rate = sample_rate
        self.inject_response_headers = inject_response_headers
        self.force_new_trace = force_new_trace
        self.json_encoder = json_encoder
        self.header_formatter = header_formatter(**header_formatter_kwargs)
