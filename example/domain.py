from typing import List

from eventsourcing.domain.model.entity import MetaDomainEntity
from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.decorators import attribute


class World(AggregateRoot):

    def __init__(self, ruler=None, **kwargs):
        super().__init__(**kwargs)
        self._views = 0
        self._history: List[str] = []
        self._ruler: str = ruler

    @property
    def history(self):
        return tuple(self._history)

    @attribute
    def ruler(self):
        """A mutable event-sourced attribute."""

    @attribute
    def views(self):
        """A mutable event-sourced attribute."""

    def storytell(self, something):
        self.__trigger_event__(World.SomethingHappened, what=something)

    def view(self, something):
        self.__trigger_event__(World.Viewed)

    class SomethingHappened(AggregateRoot.Event):
        def mutate(self, obj):
            obj._history.append(self.what)

    class Viewed(AggregateRoot.Event):
        def mutate(self, obj):
            obj._views += 1
