from devtools import debug

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


# TODO: There will be cases in which commands fail imediately
# for "logical reasons", eg input inconsistency, authorization,
# etc. Those cases should return those errors in a generic way.
# IDEA: If the viewer should see the error, include the error as a
# field in the response payload.
# AKA: if it should be seen it's not an error.

@mutation.field("createOrder")
async def resolve_create_order(obj, info, input):
    return dict(command=dict(
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
