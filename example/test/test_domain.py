from uuid import uuid4

import example.domain


def test_create_order_command():

    # Create a "create order" command.
    cmd = example.domain.CreateOrder.create()

    # Check the initial values.
    assert cmd.order_id is None
    assert cmd.is_done is False

    # Assign an order ID.
    order_id = uuid4()
    cmd.order_id = order_id
    assert cmd.order_id == order_id

    # Mark the command as "done".
    cmd.done()
    assert cmd.is_done is True

    # Check the events.
    events = cmd.__batch_pending_events__()
    assert len(events) == 3
    assert isinstance(events[0], example.domain.CreateOrder.Created)
    assert isinstance(events[1], example.domain.CreateOrder.AttributeChanged)
    assert isinstance(events[2], example.domain.CreateOrder.Done)
