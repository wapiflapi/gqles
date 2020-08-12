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

    PossibleExceptions = (OperationalError, RecordConflictError)

    # TODO: developer contention on the Commnds process?
    # if this is a single entry point how to deal with
    #  - code activity (development contention)
    #    there is no logic, it should be declarative from
    #    the dev teams and serve as a registry.
    #    MUCH like the schema first graphql,
    #    There might be something with FEDERATION
    #  - scale / distribution
    #    if this is just firing messages not doing logici,
    #    simply reccording the command it's FINE.

    # TODO: We actually need some stuff (items, amoutn, etc. INPUT) in the order.

    # TODO: Is this the thing we want to expose on GQL? -> YES
    # The following is not part of the policy!
    # it's the "user interface" entry point.
    # that's why it's different.
    @staticmethod
    @retry(
        PossibleExceptions,
        max_attempts=10,
        wait=0.01,
    )
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


# TODO: put these comments where they needs to go.
# -> spoiler, not here.
# Some thoughts from wapi:
# Maybe it makes sense to have one instance of Commands application
# for each "Web worker" (instance of FastAPI), and then have the "Core"
# be independent of that, for example with thespian.
# The question is then what to do with Reporting type processes?
# They want to expose through FastAPI, and ideally update their state
# close to that?
# /!\ Reply from john
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
