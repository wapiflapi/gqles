import ariadne

import sqlalchemy

import gqles.scalars

import example.policies


mutation = ariadne.ObjectType("Mutation")
query = ariadne.ObjectType("Query")

types = [
    mutation,
    query,
    *gqles.scalars.types,
]



@mutation.field("createOrder")
async def resolve_create_order(obj, info, input):
    return dict(created=dict(
        uuid=example.policies.Commands.create_order(),
    ))


@query.field("db")
async def resolve_db(obj, info):

    insp = sqlalchemy.inspect(example.database.engine)

    return [dict(
        name=table,
        columns=[dict(
            name=c["name"],
            type=repr(c["type"]),
        ) for c in insp.get_columns(table)]
    ) for table in insp.get_table_names()]


type_defs = ariadne.load_schema_from_path("example/sdl/")

# TODO: gqles should at least give a warning if not everything is
# passed on here I've had problems multiple times forgetting to add
# something.
schema = ariadne.make_executable_schema(
    type_defs,
    *types,
)
