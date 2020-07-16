import threading

from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from sqlalchemy.orm import scoped_session

import example.database


_application = None
lock = threading.Lock()


def get_current_scope():
    pass


ScopedSession = scoped_session(
    example.database.SessionLocal,
    scopefunc=get_current_scope,
)


def construct_application(**kwargs):
    return SQLAlchemyApplication(
        session=ScopedSession,
        **kwargs,
    )


def get_application():
    global _application
    if _application is None:
        lock.acquire()
        try:
            # Check again to avoid a TOCTOU bug.
            if _application is None:
                _application = construct_application()
        finally:
            lock.release()

    yield _application

    if _application is not None:
        _application.close()
        _application = None
