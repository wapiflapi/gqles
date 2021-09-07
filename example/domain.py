from devtools import debug

import uuid

from typing import Optional, Any

from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.command import Command
from eventsourcing.domain.model.decorators import attribute, subclassevents

from gqles.model import Model


@subclassevents
class Order(Model, AggregateRoot):

    command_id: uuid.UUID
    reservation_id: Optional[uuid.UUID]
    payment_id: Optional[uuid.UUID]

    @classmethod
    def create(cls, command_id):
        return cls.__create__(command_id=command_id)

    class Reserved(AggregateRoot.Event):
        def mutate(self, order: "Order"):
            order.reservation_id = self.reservation_id

    class Paid(AggregateRoot.Event):
        def mutate(self, order: "Order"):
            order.payment_id = self.payment_id

    @property
    def is_reserved(self):
        return self.reservation_id is not None

    @property
    def is_paid(self):
        return self.payment_id is not None

    def set_is_reserved(self, reservation_id):
        assert not self.is_reserved, f"Order ${self.id} already reserved."
        self.__trigger_event__(
            Order.Reserved, reservation_id=reservation_id
        )

    def set_is_paid(self, payment_id):
        assert not self.is_paid, "Order {} already paid.".format(self.id)
        self.__trigger_event__(
            self.Paid, payment_id=payment_id, command_id=self.command_id
        )


@subclassevents
class CreateOrder(Model, Command):

    @classmethod
    def create(cls):
        return cls.__create__()

    @attribute
    def order_id(self):
        pass


@subclassevents
class Reservation(Model, AggregateRoot):

    order_id: uuid.UUID

    @classmethod
    def create(cls, order_id):
        return cls.__create__(order_id=order_id)


@subclassevents
class Payment(Model, AggregateRoot):

    order_id: uuid.UUID

    @classmethod
    def create(cls, order_id):
        return cls.__create__(order_id=order_id)
