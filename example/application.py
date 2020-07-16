import threading

from eventsourcing.application.sqlalchemy import SQLAlchemyApplication

import example.database


class Application(SQLAlchemyApplication):
    def __init__(self, **kwargs):
        super().__init__(
            session=example.database.ScopedSession,
            **kwargs,
        )


_application = None


async def init_application(**kwargs):
    global _application
    if _application is not None:
        raise AssertionError("init_application() has already been called")
    _application = Application(**kwargs)
    return _application

async def get_application():
    if _application is None:
        raise AssertionError("init_application() must be called first")
    return _application


async def close_application():
    global _application
    if _application is not None:
        _application.close()
        _application = None
