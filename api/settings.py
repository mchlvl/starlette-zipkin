import os
from sys import platform

GRAPHQL_ROUTE = "/graphql"
DEBUG = os.getenv("DEBUG", False if "linux" in platform else True)
JAEGER_HOST = os.getenv("JAEGER_HOST", "localhost")
JAEGER_PORT = int(os.getenv("JAEGER_PORT", "9411"))
JAEGER_SERVICE_NAME = "service_name"
