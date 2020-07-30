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

import example.application
import example.scalars


type_defs = ariadne.load_schema_from_path("example/sdl/")

state_insight = ariadne.InterfaceType("StateInsight")

query = ariadne.ObjectType("Query")
application = ariadne.ObjectType("Application")
originator = ariadne.ObjectType("Originator")
insight = ariadne.ObjectType("Insight")
event = ariadne.ObjectType("Event")


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



@query.field("applications")
async def resolve_applications(obj, info):
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
        applicationNames=None,
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
    for application in system_runner.processes.values():
        name = application.name
        if applicationNames is not None and name not in applicationNames:
            continue

        cursor_data[name] = after_data.get(name, before_data.get(name))

        items, hasprev, hasnext = paginate_notifications(
            application.notification_log,
            last=last, first=first,
            before=before_data.get(name), after=after_data.get(name),
        )

        has_previous_page = has_previous_page or hasprev
        has_next_page = has_next_page or hasnext

        streams.append([(
            application,
            position,
            notification,
            application.event_store.event_mapper.event_from_topic_and_state(
                notification["topic"], notification["state"],
            ),
        ) for position, notification in items])

    edges = []
    function, idx, limit = (
        (max, -1, last) if first is None else
        (min, 0, first)
    )

    while any(streams) and len(edges) < limit:

        application, position, notification, event = function(
            filter(None, streams),
            key=lambda s: s[idx][3].timestamp,
        ).pop(idx)

        cursor_data[application.name] = position

        edges.append(dict(
            cursor=to_cursor(cursor_data),
            application=application,
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
                    application,
                    event,
                    notification["topic"],
                    notification["state"]
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


@query.field("event")
async def resolve_query_event(
        obj, info, applicationName, originatorId, originatorVersion,
):
    system_runner = await example.application.get_system_runner()
    try:
        application = system_runner.processes[applicationName]
    except KeyError:
        return None

    print((originatorId, type(originatorId)))
    event = application.event_store.get_event(originatorId, originatorVersion)

    return get_event_data(
        application,
        event,
        *application.event_store.event_mapper.get_item_topic_and_state(
            event.__class__, event.__dict__,
        ),
    )


def get_originator_data(application, originator_id):

    event = application.event_store.get_most_recent_event(
        originator_id=originator_id,
    )

    if event is None:
        return None

    return dict(
        application=application,
        originatorId=event.originator_id,
        last=lambda _, e=event: get_event_data(
            application,
            e,
            *application.event_store.event_mapper.get_item_topic_and_state(
                e.__class__, e.__dict__,
            ),
        ),
    )



@query.field("insights")
async def resolve_query_insights(obj, info, uuids):
    system_runner = await example.application.get_system_runner()

    # TODO: This is very naive, how do we batch this?
    def resolve_insight(candidate):
        for application in system_runner.processes.values():
            originator = get_originator_data(application, candidate)
            if not originator:
                continue
            return dict(
                applicationName=application.name,
                originator=originator,
            )

    return [resolve_insight(candidate) for candidate in uuids]


@application.field("id")
async def resolve_applications_id(obj, info):
    return obj.name


@application.field("notifications")
async def resolve_applications_notifications(
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
        application=obj,
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


@application.field("originator")
async def resolve_applications_events(
        obj, info, originatorId,
):
    return get_originator_data(obj, originatorId)


@originator.field("events")
async def resolve_applications_events(
        obj, info, last, first=None, before=None, after=None,
):

    application = obj["application"]
    originatorId = obj["originatorId"]

    @from_base64
    def from_cursor(cursor):
        return int(cursor) if cursor is not None else None

    @to_base64
    def to_cursor(position):
        return str(position) if position is not None else None

    events, has_prev, has_next = paginate_events(
        application.event_store, originatorId,
        last=last, first=first,
        before=from_cursor(before),
        after=from_cursor(after),
    )

    edges = [dict(
        cursor=to_cursor(originator_version),
        # Careful with the lambda scoping! We need to make a copy
        # of the current notification in the lambda's scope.
        node=lambda _, e=event: get_event_data(
            application,
            e,
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


def get_event_data(application, event, topic, state):

    return dict(
        application=application,
        event=event,
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


async def _resolve_event_events(
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


@event.field("previousEvents")
async def resolve_event_previous_events(
        obj, info, last, before=None,
):

    try:
        originatorVersion = obj["originatorVersion"]
    except KeyError:
        return None

    return await _resolve_event_events(
        obj, info, first=None, last=last, after=None,
        before=originatorVersion if before is None else before,
    )


@event.field("nextEvents")
async def resolve_event_next_events(
        obj, info, first, after=None,
):

    try:
        originatorVersion = obj["originatorVersion"]
    except KeyError:
        return None

    return await _resolve_event_events(
        obj, info, first=first, last=None, before=None,
        after=originatorVersion if after is None else after,
    )


@event.field("id")
async def resolve_event_id(obj, info):
    return "%s/%s/%d" % (
        obj["application"].name,
        obj["originatorId"],
        obj["originatorVersion"],
    )

@event.field("applicationName")
async def resolve_event_id(obj, info):
    return obj["application"].name

@state_insight.type_resolver
def resolve_state_insight_type(obj, *_):
    if isinstance(obj.get("uuid"), uuid.UUID):
        return "StateInsightUUID"
    if isinstance(obj.get("datetime"), datetime.datetime):
        return "StateInsightDatetime"
    if isinstance(obj.get("json"), str):
        return "StateInsightJSON"
    return None


@event.field("stateInsight")
async def resolve_event_id(obj, info):

    def decode(key, value):

        if isinstance(value, uuid.UUID):
            return dict(key=key, text=str(value), uuid=value)
        if isinstance(value, datetime.datetime):
            return dict(key=key, text=str(value), datetime=value)
        if key == "timestamp" and isinstance(value, decimal.Decimal):
            dt = datetime.datetime.fromtimestamp(
                value, datetime.timezone.utc,
            )
            return dict(key=key, text=str(dt), datetime=dt)

        try:
            return dict(key=key, text=str(value), json=json.dumps(value))
        except TypeError:
            pass

        return dict(key=key, text=str(value))


    return [
        decode(key, value)
        for key, value in obj["event"].__dict__.items()
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


# TODO: gqles should at least give a warning if not everything is
# passed on here I've had problems multiple times forgetting to add
# something.
schema = ariadne.make_executable_schema(
    type_defs,
    *example.scalars.types,
    query,
    application,
    originator,
    event,
    state_insight,
    insight,
)
