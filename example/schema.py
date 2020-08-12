import base64
import datetime
import decimal
import functools
import json
import uuid

import ariadne

import eventsourcing.utils.topic
import eventsourcing.application.notificationlog

import sqlalchemy

import gqles.schema

from gqles.application import get_system_runner



query = ariadne.ObjectType("Query")

types = [
    query,
]

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
