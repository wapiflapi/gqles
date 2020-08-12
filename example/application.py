from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.system.runner import SingleThreadedRunner

import example.database

import example.domain
import example.policies


class Application(SQLAlchemyApplication):
    def __init__(self, session=None, **kwargs):
        # Sometimes session is passed as None explicitly,
        # we want to provide a default in that case.
        # TODO: When and why is it passed None? And why default?
        super().__init__(
            session=session or example.database.ScopedSession,
            **kwargs,
        )


class SystemRunner(SingleThreadedRunner):
    def __init__(self, **kwargs):
        super().__init__(
            system=example.policies.system,
            infrastructure_class=Application,
            setup_tables=True,
        )
