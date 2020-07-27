import base64
import json

import ariadne

import eventsourcing.utils.topic
import eventsourcing.utils.times
import eventsourcing.application.notificationlog

import starlette_context

import sqlalchemy

import example.application


type_defs = ariadne.load_schema_from_path("example/sdl/")

datetime_scalar = ariadne.ScalarType("Datetime")

query = ariadne.ObjectType("Query")

process_application = ariadne.ObjectType("ProcessApplication")

@datetime_scalar.serializer
def serialize_datetime(value):
    return value.isoformat()


@query.field("processApplications")
async def resolve_process_applications(obj, info):
    system_runner = await example.application.get_system_runner()
    return system_runner.processes.values()


@process_application.field("notifications")
async def resolve_process_applications_notifications(
        obj, info, last, first=None, before=None, after=None,
):

    def from_cursor(cursor):
        return int(cursor)

    def to_cursor(position):
        return str(position)

    reader = eventsourcing.application.notificationlog.NotificationLogReader(
        obj.notification_log,
        use_direct_query_if_available=True,
    )

    next_position = obj.notification_log.get_next_position()

    if before is not None:
        position = max(0, from_cursor(before) - last)
        advance_by = min(last, from_cursor(before))
    elif after is not None:
        position = from_cursor(after) + 1
        advance_by = first if first is not None else last
    elif first is not None:
        position = 0
        advance_by = first
    else:
        position = max(0, next_position - last)
        advance_by = last

    reader.seek(position)
    notifications = reader.list_notifications(advance_by=advance_by)

    def foobar(x):
        print("Resolving using %s" % (x,))

    return dict(
        pageInfo=dict(
            hasPreviousPage=position > 0,
            hasNextPage=position + advance_by < next_position,
            startCursor=to_cursor(position),
            endCursor=to_cursor(position + len(notifications) - 1),
        ),
        edges=[dict(
            cursor=to_cursor(position + offset),
            node=dict(
                applicationName=obj.name,
                notificationId=notification["id"],
                originatorId=notification["originator_id"],
                originatorVersion=notification["originator_version"],
                topic=notification["topic"],
                state=base64.b64encode(notification["state"]).decode("utf8"),
                causalDependencies=notification["causal_dependencies"],
                # Careful with the lambda scoping! We need to make a copy
                # of the current notification in the lambda's scope.
                event=lambda _, n=notification: event_data_from_event(
                    obj.event_store.event_mapper.event_from_topic_and_state(
                        n["topic"], n["state"],
                    ),
                ),
            ),
        ) for offset, notification in enumerate(notifications)],
    )


@process_application.field("events")
async def resolve_process_applications_events(
        obj, info, originatorId, last, first=None, before=None, after=None,
):

    def from_cursor(cursor):
        return int(cursor)

    def to_cursor(position):
        return str(position)

    is_ascending = after is not None
    limit = first if first is not None else last

    events = list(obj.event_store.iter_events(
        originator_id=originatorId,
        gt=from_cursor(after) if after else None,
        lt=from_cursor(before) if before else None,
        limit=limit+1,
        is_ascending=is_ascending,
    ))

    has_more = len(events) > limit
    events = events[:limit]
    if not is_ascending:
        events = list(reversed(events))

    return dict(
        pageInfo=dict(
            hasPreviousPage=False if is_ascending else has_more,
            hasNextPage=has_more if is_ascending else False,
            startCursor=events and events[0].originator_version,
            endCursor=events and events[-1].originator_version,
        ),
        edges=[dict(
            cursor=to_cursor(event.originator_version),
            node=event_data_from_event(event),
        ) for event in events],
    )


def event_data_from_event(event):
    return dict(
        topic=eventsourcing.utils.topic.get_topic(type(event)),
        originatorId=event.originator_id,
        originatorVersion=event.originator_version,
        timestamp=eventsourcing.utils.times.datetime_from_timestamp(
            event.timestamp,
        ),
    )


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


# TODO: gqles should at least give a warning if not everything is passed on here
# I've had problems multiple times forgetting to add something.
schema = ariadne.make_executable_schema(
    type_defs,
    datetime_scalar,
    query,
    process_application,
)
