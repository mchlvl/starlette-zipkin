from graphene import ObjectType
from graphene import Field
from graphene import String


class Query(ObjectType):
    raise_exception = Field(
        String,
        description="Raises exception by performing 1/0 inside the resolver.",
    )

    async def resolve_raise_exception(parent, info, **kw):
        1 / 0
        return str(kw)
