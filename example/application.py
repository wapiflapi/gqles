from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.system.runner import SingleThreadedRunner

import example.database

import example.domain
import example.policies


class Application(SQLAlchemyApplication):
    def __init__(self, session=None, **kwargs):
        # Sometimes session is passed as None explicitly,
        # we want to provide a default in that case.
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


_system_runner = None


async def init_system_runner(**kwargs):
    global _system_runner
    if _system_runner is not None:
        raise AssertionError("init_system_runner() has already been called")
    _system_runner = SystemRunner(**kwargs)
    _system_runner.start()
    return _system_runner


async def get_system_runner():
    if _system_runner is None:
        raise AssertionError("init_system_runner() must be called first")
    return _system_runner


async def close_system_runner():
    global _system_runner
    if _system_runner is not None:
        _system_runner.close()
        _system_runner = None
