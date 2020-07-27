from eventsourcing.application.process import ProcessApplication
from eventsourcing.application.decorators import applicationpolicy

from eventsourcing.application.command import CommandProcess
from eventsourcing.domain.model.decorators import retry
from eventsourcing.exceptions import OperationalError, RecordConflictError

from eventsourcing.system.definition import System


import example.domain


class Orders(ProcessApplication):

    @applicationpolicy
    def policy(self, repository, event):
        """Do nothing by default."""

    @policy.register(example.domain.CreateOrder.Created)
    def _(self, repository, event):
        return self._create_order(command_id=event.originator_id)

    @policy.register(example.domain.Reservation.Created)
    def _(self, repository, event):
        self._set_order_is_reserved(repository, event)

    @policy.register(example.domain.Payment.Created)
    def _(self, repository, event):
        self._set_order_is_paid(repository, event)

    @staticmethod
    def _create_order(command_id):
        return example.domain.Order.create(command_id=command_id)

    def _set_order_is_reserved(self, repository, event):
        order = repository[event.order_id]
        assert not order.is_reserved
        order.set_is_reserved(event.originator_id)

    def _set_order_is_paid(self, repository, event):
        order = repository[event.order_id]
        assert not order.is_paid
        order.set_is_paid(event.originator_id)


class Reservations(ProcessApplication):

    @applicationpolicy
    def policy(self, repository, event):
        """Do nothing by default."""

    @policy.register(example.domain.Order.Created)
    def _(self, repository, event):
        return self._create_reservation(event.originator_id)

    @staticmethod
    def _create_reservation(order_id):
        return example.domain.Reservation.create(order_id=order_id)


class Payments(ProcessApplication):

    @applicationpolicy
    def policy(self, repository, event):
        """Do nothing by default."""

    @policy.register(example.domain.Order.Reserved)
    def _(self, repository, event):
        order_id = event.originator_id
        return self._create_payment(order_id)

    @staticmethod
    def _create_payment(order_id):
        return example.domain.Payment.create(order_id=order_id)


class Commands(CommandProcess):

    @staticmethod
    @retry((OperationalError, RecordConflictError), max_attempts=10, wait=0.01)
    def create_order():
        cmd = example.domain.CreateOrder.create()
        cmd.__save__()
        return cmd.id

    @applicationpolicy
    def policy(self, repository, event):
        """Do nothing by default."""

    @policy.register(example.domain.Order.Created)
    def _(self, repository, event):
        cmd = repository[event.command_id]
        cmd.order_id = event.originator_id

    @policy.register(example.domain.Order.Paid)
    def _(self, repository, event):
        cmd = repository[event.command_id]
        cmd.done()


# Some thoughts from wapi:
# Maybe it makes sense to have one instance of Commands application
# for each "Web worker" (instance of FastAPI), and then have the "Core"
# be independent of that, for example with thespian.
# The question is then what to do with Reporting type processes?
# They want to expose through FastAPI, and ideally update their state
# close to that?


# Reply from john
# - multiple web app instances: simplest thing is each has a command
# application writing to the same 'pipeline id', might help to have
# multiple pipelines reducing contention on writing log sequences.
# - assuming one pipeline id: one instance of each downstream process
# application process. Like micro services except the call is a prompt.
# - multiple pipelines adds another level of complexity.


system = System(
    Commands | Orders | Commands,
    Orders | Reservations | Orders,
    Orders | Payments | Orders
)
