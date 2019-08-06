import traceback
from graphql import GraphQLError

from api.utils import get_fields
from api.middlewares.zipkin import get_root_span, init_tracer


class GrapheneZipkinMiddleware(object):
    async def resolve(self, next, root, info, **kwargs):

        if self.should_not_trace(info):
            return next(root, info, **kwargs)
        else:
            root_span = get_root_span()
            tracer = await init_tracer()
            with tracer.new_child(root_span.context) as span:
                span.name(info.field_name)
                span.tag("graphql.fields", get_fields(info))
                span.tag("component", "graphql")
                span.tag("graphql.parentType", info.parent_type.name)
                span.tag("graphql.path", info.path)
                if kwargs:
                    for kwarg, value in kwargs.items():
                        span.tag(f"graphql.param.{kwarg}", value)

                def on_error(error):
                    span.tag("error", True)
                    tb = traceback.format_exc()
                    span.annotate(error)
                    span.annotate(tb)
                    raise GraphQLError(error)

                info.context.update({"span": span})
                result = await next(root, info, **kwargs).catch(on_error)
                return result

    def should_not_trace(self, info):
        if (
            info.field_name not in info.parent_type.fields
            or "__schema" in info.path
        ):
            return True
        else:
            return False
