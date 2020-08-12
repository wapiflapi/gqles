import uuid

import ariadne


datetime_scalar = ariadne.ScalarType("Datetime")
uuid_scalar = ariadne.ScalarType("UUID")

# This is exported so that it can be added to the schema.
types = [datetime_scalar, uuid_scalar]


@datetime_scalar.serializer
def serialize_datetime(value):
    return value.isoformat()


@uuid_scalar.serializer
def serialize_uuid(value):
    return str(value)


@uuid_scalar.value_parser
def parse_uuid_value(value):
    if value:
        return uuid.UUID(value)


@uuid_scalar.literal_parser
def parse_uuid_literal(ast):
    return parse_uuid_value(str(ast.value))
