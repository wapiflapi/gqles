import base64
import datetime
import functools
import json

import ariadne

import eventsourcing.utils.topic
import eventsourcing.application.notificationlog

import sqlalchemy

import example.application


type_defs = ariadne.load_schema_from_path("example/sdl/")

datetime_scalar = ariadne.ScalarType("Datetime")

query = ariadne.ObjectType("Query")
process_application = ariadne.ObjectType("ProcessApplication")
aggregate_root_event = ariadne.ObjectType("AggregateRootEvent")


BASE64_CURSORS = True


def to_base64(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        result = f(*args, **kwargs)
        if result is not None:
            result = base64.b64encode(result.encode("utf8")).decode("utf8")
        return result
    return wrapper if BASE64_CURSORS else f


def from_base64(f):
    @functools.wraps(f)
    def wrapper(data, *args, **kwargs):
        if data is not None:
            data = base64.b64decode(data.encode("utf8")).decode("utf8")
        return f(data, *args, **kwargs,)
    return wrapper if BASE64_CURSORS else f


@datetime_scalar.serializer
def serialize_datetime(value):
    return value.isoformat()


@query.field("processApplications")
async def resolve_process_applications(obj, info):
    system_runner = await example.application.get_system_runner()
    return system_runner.processes.values()


def paginate_notifications(
        notificationlog, last, first=None, before=None, after=None,
):
    """
    Paginate through a notification log.

    Return:
        ([[position, notification], ...], has_prev, has_next)
    """

    reader = eventsourcing.application.notificationlog.NotificationLogReader(
        notificationlog,
        use_direct_query_if_available=True,
    )

    next_position = notificationlog.get_next_position()

    if before is not None:
        position = max(0, before - last)
        advance_by = min(last, before)
    elif after is not None:
        position = after + 1
        advance_by = first if first is not None else last
    elif first is not None:
        position = 0
        advance_by = first
    else:
        position = max(0, next_position - last)
        advance_by = last

    reader.seek(position)
    notifications = reader.list_notifications(advance_by=advance_by)

    has_prev = position > 0
    has_next = position + advance_by < next_position

    return [(
        position + offset, notification
    ) for offset, notification in enumerate(notifications)], has_prev, has_next


@query.field("notifications")
async def resolve_notifications(
        obj, info,
        last, first=None, before=None, after=None,
        processApplications=None,
):

    @from_base64
    def from_cursor(cursor):
        return json.loads(cursor) if cursor is not None else None

    @to_base64
    def to_cursor(data):
        return json.dumps(data) if data is not None else None

    before_data = from_cursor(before) or {}
    after_data = from_cursor(after) or {}

    has_previous_page = False
    has_next_page = False

    streams = []

    cursor_data = {}

    system_runner = await example.application.get_system_runner()
    for process in system_runner.processes.values():
        name = process.name
        if processApplications is not None and name not in processApplications:
            continue

        cursor_data[name] = after_data.get(name, before_data.get(name))

        items, hasprev, hasnext = paginate_notifications(
            process.notification_log,
            last=last, first=first,
            before=before_data.get(name), after=after_data.get(name),
        )

        has_previous_page = has_previous_page or hasprev
        has_next_page = has_next_page or hasnext

        streams.append([(
            process,
            position,
            notification,
            process.event_store.event_mapper.event_from_topic_and_state(
                notification["topic"], notification["state"],
            ),
        ) for position, notification in items])

    edges = []
    function, idx, limit = (
        (max, -1, last) if first is None else
        (min, 0, first)
    )

    while any(streams) and len(edges) < limit:

        process, position, notification, event = function(
            filter(None, streams),
            key=lambda s: s[idx][3].timestamp,
        ).pop(idx)

        cursor_data[process.name] = position

        edges.append(dict(
            cursor=to_cursor(cursor_data),
            processApplication=process,
            node=dict(
                notificationId=notification["id"],
                originatorId=notification["originator_id"],
                originatorVersion=notification["originator_version"],
                topic=notification["topic"],
                causalDependencies=notification["causal_dependencies"],
                # Careful with the lambda scoping! We need to make a copy
                # of the current notification in the lambda's scope.
                state=lambda _, n=notification: base64.b64encode(
                    n["state"]).decode("utf8"),
                event=get_event_data(
                    process, event, notification["topic"], notification["state"]
                ),
            ),
        ))

    if idx == -1:
        edges = edges[::-1]
        has_previous_page = has_previous_page or any(streams)
    else:
        has_next_page = has_next_page or any(streams)

    return dict(
        pageInfo=dict(
            hasPreviousPage=has_previous_page,
            hasNextPage=has_next_page,
            startCursor=edges[0]["cursor"] if edges else None,
            endCursor=edges[-1]["cursor"] if edges else None,
        ),
        edges=edges,
    )


@process_application.field("id")
async def resolve_process_applications_id(obj, info):
    return obj.name


@process_application.field("notifications")
async def resolve_process_applications_notifications(
        obj, info, last, first=None, before=None, after=None,
):

    @from_base64
    def from_cursor(cursor):
        return int(cursor) if cursor is not None else None

    @to_base64
    def to_cursor(position):
        return str(position) if position is not None else None

    items, has_prev, has_next = paginate_notifications(
        obj.notification_log,
        last=last, first=first,
        before=from_cursor(before), after=from_cursor(after)
    )

    edges = [dict(
        cursor=to_cursor(position),
        processApplication=obj,
        node=dict(
            notificationId=notification["id"],
            originatorId=notification["originator_id"],
            originatorVersion=notification["originator_version"],
            topic=notification["topic"],
            # Careful with the lambda scoping! We need to make a copy
            # of the current notification in the lambda's scope.
                state=lambda _, n=notification: base64.b64encode(
                    n["state"]).decode("utf8"),
            causalDependencies=notification["causal_dependencies"],
            # Careful with the lambda scoping! We need to make a copy
            # of the current notification in the lambda's scope.
                event=lambda _, n=notification: get_event_data(
                    obj,
                    obj.event_store.event_mapper.event_from_topic_and_state(
                        n["topic"], n["state"],
                    ),
                    n["topic"],
                    n["state"]
                ),
        ),
    ) for position, notification in items]

    return dict(
        pageInfo=dict(
            hasPreviousPage=has_prev,
            hasNextPage=has_next,
            startCursor=edges[0]["cursor"] if edges else None,
            endCursor=edges[-1]["cursor"] if edges else None,
        ),
        edges=edges,
    )


def paginate_events(
        eventstore, originatorId, last, first=None, before=None, after=None,
):
    """
    Paginate through an event store.

    Return:
        ([[position, notification], ...], has_prev, has_next)
    """

    is_ascending = after is not None
    limit = first if first is not None else last

    events = list(eventstore.iter_events(
        originator_id=originatorId,
        gt=after,
        lt=before,
        limit=limit+1,
        is_ascending=is_ascending,
    ))

    has_more = len(events) > limit
    events = events[:limit]
    if not is_ascending:
        events = list(reversed(events))

    return (
        [(event.originator_version, event) for event in events],
        (after is not None) or (events and events[0].originator_version > 0),
        (before is not None) or has_more,
    )


@process_application.field("events")
async def resolve_process_applications_events(
        obj, info, originatorId, last, first=None, before=None, after=None,
):

    @from_base64
    def from_cursor(cursor):
        return int(cursor) if cursor is not None else None

    @to_base64
    def to_cursor(position):
        return str(position) if position is not None else None

    events, has_prev, has_next = paginate_events(
        obj.event_store, originatorId,
        last=last, first=first,
        before=from_cursor(before),
        after=from_cursor(after),
    )

    edges = [dict(
        cursor=to_cursor(event.originator_version),
        # Careful with the lambda scoping! We need to make a copy
        # of the current notification in the lambda's scope.
        node=lambda _, e=event: get_event_data(
            obj,
            e,
            *obj.event_store.event_mapper.get_item_topic_and_state(
                e.__class__, e.__dict__,
            ),
        ),
    ) for event in events]

    return dict(
        edges=edges,
        pageInfo=dict(
            hasPreviousPage=has_prev,
            hasNextPage=has_next,
            startCursor=edges[0]["cursor"] if edges else None,
            endCursor=edges[-1]["cursor"] if edges else None,
        ),
    )


def get_event_data(application, event, topic, state):

    return dict(
        application=application,
        topic=topic,
        # Careful with the lambda scoping! We need to make a copy
        # of the current notification in the lambda's scope.
        # In this case it's not needed, but keep it in case this
        # gets copy/pasted somewhere else.
        state=lambda _, s=state: base64.b64encode(s).decode("utf8"),
        originatorId=event.originator_id,
        originatorVersion=event.originator_version,
        timestamp=datetime.datetime.fromtimestamp(
            event.timestamp, datetime.timezone.utc,
        ),
    )


async def _resolve_aggregate_root_event_events(
        obj, info, first=None, last=None, before=None, after=None
):

    try:
        application = obj["application"]
        originatorId = obj["originatorId"]
    except KeyError:
        return None

    @from_base64
    def from_cursor(cursor):
        return int(cursor) if cursor is not None else None

    @to_base64
    def to_cursor(position):
        return str(position) if position is not None else None

    events, has_prev, has_next = paginate_events(
        application.event_store,
        originatorId,
        first=first,
        last=last,
        before=before,
        after=after,
    )

    edges = [dict(
        cursor=to_cursor(originator_version),
        # Careful with the lambda scoping! We need to make a copy
        # of the current notification in the lambda's scope.
        node=lambda _, e=event: get_event_data(
            application, e,
            *application.event_store.event_mapper.get_item_topic_and_state(
                e.__class__, e.__dict__,
            ),
        ),
    ) for (originator_version, event) in events]

    return dict(
        edges=edges,
        pageInfo=dict(
            hasPreviousPage=has_prev,
            hasNextPage=has_next,
            startCursor=edges[0]["cursor"] if edges else None,
            endCursor=edges[-1]["cursor"] if edges else None,
        ),
    )


@aggregate_root_event.field("previousEvents")
async def resolve_aggregate_root_event_previous_events(
        obj, info, last, before=None,
):

    try:
        originatorVersion = obj["originatorVersion"]
    except KeyError:
        return None

    return await _resolve_aggregate_root_event_events(
        obj, info, first=None, last=last, after=None,
        before=originatorVersion if before is None else before,
    )


@aggregate_root_event.field("nextEvents")
async def resolve_aggregate_root_event_next_events(
        obj, info, first, after=None,
):

    try:
        originatorVersion = obj["originatorVersion"]
    except KeyError:
        return None

    return await _resolve_aggregate_root_event_events(
        obj, info, first=first, last=None, before=None,
        after=originatorVersion if after is None else after,
    )


@aggregate_root_event.field("id")
async def resolve_aggregate_root_event_id(obj, info):
    return "%s/%s/%d" % (
        obj["application"].name,
        obj["originatorId"],
        obj["originatorVersion"],
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


# TODO: gqles should at least give a warning if not everything is
# passed on here I've had problems multiple times forgetting to add
# something.
schema = ariadne.make_executable_schema(
    type_defs,
    datetime_scalar,
    query,
    process_application,
    aggregate_root_event,
)
