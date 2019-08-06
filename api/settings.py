import os
from sys import platform

GRAPHQL_ROUTE = "/graphql"
DEBUG = os.getenv("DEBUG", False if "linux" in platform else True)
ZIPKIN_AGENT_HOST = os.getenv("ZIPKIN_AGENT_HOST", "localhost")
ZIPKIN_AGENT_PORT = int(os.getenv("ZIPKIN_AGENT_PORT", "9411"))
ZIPKIN_SERVICE_NAME = "service_name"
