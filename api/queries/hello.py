import graphene
import asyncio


class Query(graphene.ObjectType):
    hello = graphene.String(
        name=graphene.String(default_value="Stranger"),
        description="Testing query returning hello <name>, while async sleeping for 5 sec.",
    )

    async def resolve_hello(self, info, name):
        await asyncio.sleep(5)
        return "Hello " + name
