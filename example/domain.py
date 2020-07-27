# coding: utf-8

from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.command import Command
from eventsourcing.domain.model.decorators import attribute

# All the domain event classes are defined explicitly on the aggregate
# root classes. This is important because the application policies
# will use the domain event classes to decide how to respond to the
# events, and if the aggregate classes use the event classes from the
# base aggregate root class, then one aggregate’s Created event can’t
# be distinguished from another’s, and the application policy won’t
# work as expected.


class Order(AggregateRoot):

    class Event(AggregateRoot.Event):
        pass

    @classmethod
    def create(cls, command_id):
        return cls.__create__(command_id=command_id)

    class Created(Event, AggregateRoot.Created):
        pass

    def __init__(self, command_id=None, **kwargs):
        super(Order, self).__init__(**kwargs)
        self.command_id = command_id
        self.reservation_id = None
        self.payment_id = None

    @property
    def is_reserved(self):
        return self.reservation_id is not None

    def set_is_reserved(self, reservation_id):
        assert not self.is_reserved, f"Order ${self.id} already reserved."
        self.__trigger_event__(
            Order.Reserved, reservation_id=reservation_id
        )

    class Reserved(Event):
        def mutate(self, order: "Order"):
            order.reservation_id = self.reservation_id

    @property
    def is_paid(self):
        return self.payment_id is not None

    def set_is_paid(self, payment_id):
        assert not self.is_paid, "Order {} already paid.".format(self.id)
        self.__trigger_event__(
            self.Paid, payment_id=payment_id, command_id=self.command_id
        )

    class Paid(Event):
        def mutate(self, order: "Order"):
            order.payment_id = self.payment_id


class CreateOrder(Command):

    class Event(Command.Event):
        pass

    @classmethod
    def create(cls):
        return cls.__create__()

    class Created(Event, Command.Created):
        pass

    @attribute
    def order_id(self):
        pass

    class AttributeChanged(Event, Command.AttributeChanged):
        pass


class Reservation(AggregateRoot):

    class Event(AggregateRoot.Event):
        pass

    @classmethod
    def create(cls, order_id):
        return cls.__create__(order_id=order_id)

    class Created(Event, AggregateRoot.Created):
        pass

    def __init__(self, order_id, **kwargs):
        super(Reservation, self).__init__(**kwargs)
        self.order_id = order_id


class Payment(AggregateRoot):

    class Event(AggregateRoot.Event):
        pass

    @classmethod
    def create(cls, order_id):
        return cls.__create__(order_id=order_id)

    class Created(Event, AggregateRoot.Created):
        pass

    def __init__(self, order_id, **kwargs):
        super(Payment, self).__init__(**kwargs)
        self.order_id = order_id
