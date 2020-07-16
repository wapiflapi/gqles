import starlette_context

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


SQLALCHEMY_DATABASE_URL = 'sqlite:///:memory:'


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=dict(
        check_same_thread=False,
    ),
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_current_scope():
    try:
        return starlette_context.context["__scope_uuid"]
    except RuntimeError:
        return None


ScopedSession = scoped_session(
    SessionLocal,
    scopefunc=get_current_scope,
)
