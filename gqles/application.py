from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.system.runner import SingleThreadedRunner


_system_runner = None


async def start_system_runner(system_runner):
    global _system_runner
    if _system_runner is not None:
        raise AssertionError("init_system_runner() has already been called")
    _system_runner = system_runner
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
