from ariadne.asgi import GraphQL

import gqles.schema


class BackstageGraphQL(GraphQL):
    def __init__(self, **kwargs):
        super().__init__(gqles.schema.schema, **kwargs)
