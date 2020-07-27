from uuid import uuid4

import example.domain
import example.policies


def test_orders_policy():

    # Prepare repository with a real Order aggregate.
    order = example.domain.Order.create(command_id=None)
    repository = {order.id: order}

    # Check order is not reserved.
    assert not order.is_reserved

    # Check order is reserved whenever a reservation is created.
    event = example.domain.Reservation.Created(
        originator_id=uuid4(), originator_topic='', order_id=order.id)
    example.policies.Orders().policy(repository, event)
    assert order.is_reserved


def test_payments_policy():

    # Prepare repository with a real Order aggregate.
    order = example.domain.Order.create(command_id=None)
    repository = {order.id: order}

    # Check payment is created whenever order is reserved.
    event = example.domain.Order.Reserved(
        originator_id=order.id, originator_version=1)
    payment = example.policies.Payments().policy(repository, event)
    assert isinstance(payment, example.domain.Payment), payment
    assert payment.order_id == order.id
