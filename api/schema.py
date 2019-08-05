import graphene

import api.queries.hello
import api.queries.raise_exception


class Query(
    api.queries.hello.Query,
    api.queries.raise_exception.Query,
    graphene.ObjectType,
):
    pass


class Mutation(graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=None)
