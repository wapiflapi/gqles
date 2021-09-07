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

    # TODO: What does it mean when a policy returns?
    # Policies must return new aggregates to the caller, but do not
    # need to return existing aggregates that have been accessed or
    # changed.
    # TODO: Can there be a linter or something to catch that?

    @policy.register(example.domain.CreateOrder.Created)
    def _create_order(self, repository, event):
        return example.domain.Order.create(
            command_id=event.originator_id,
        )

    @policy.register(example.domain.Reservation.Created)
    def _set_order_is_reserved(self, repository, event):
        order = repository[event.order_id]
        assert not order.is_reserved
        order.set_is_reserved(event.originator_id)

    @policy.register(example.domain.Payment.Created)
    def _set_order_is_paid(self, repository, event):
        order = repository[event.order_id]
        assert not order.is_paid
        order.set_is_paid(event.originator_id)


class Reservations(ProcessApplication):

    @applicationpolicy
    def policy(self, repository, event):
        """Do nothing by default."""

    @policy.register(example.domain.Order.Created)
    def _create_reservation(self, repository, event):
        return example.domain.Reservation.create(
            order_id=event.originator_id,
        )


class Payments(ProcessApplication):

    @applicationpolicy
    def policy(self, repository, event):
        """Do nothing by default."""

    @policy.register(example.domain.Order.Reserved)
    def _create_payment(self, repository, event):
        return example.domain.Payment.create(
            order_id=event.originator_id,
        )


class Commands(CommandProcess):

    @staticmethod
    def robust_interface(**kwargs):
        return retry(
            (OperationalError, RecordConflictError),
            max_attempts=10,
            wait=0.01,
        )

    @staticmethod
    @robust_interface()
    def create_order():
        cmd = example.domain.CreateOrder.create()
        cmd.__save__()
        return cmd.id

    @applicationpolicy
    def policy(self, repository, event):
        """Do nothing by default."""

    @policy.register(example.domain.Order.Created)
    def _set_order_id(self, repository, event):
        cmd = repository[event.command_id]
        cmd.order_id = event.originator_id

    @policy.register(example.domain.Order.Paid)
    def _set_done(self, repository, event):
        cmd = repository[event.command_id]
        cmd.done()


system = System(
    Commands | Orders | Commands,
    Orders | Reservations | Orders,
    Orders | Payments | Orders
)
