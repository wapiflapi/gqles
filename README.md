# GQLDLES

## Mission Statement

Make it harder to write non sustainable code.

`create-react-app` for scalable backends in python.

## What is this about?

This is experimentation with the following ideas:
  - CQRS
  - dataloaders
  - graphQL
  - eventsourcing


## Questions

  - [ ] Why is eventsourcing not async?
  - [ ] how do migrationsn work (eg sqlalchemy to cassandra)

## Loose Roadmap / ideas

  - [ ] eventsourcing visualisation: A document per topic/aggregate?
  - [ ] handle boiler plate
  - [ ] scale between memory, local, remote, services.
  - [ ] switchable backends, dev mode
  - [ ] federated graphql
  - [ ] everything is "public" and accessible, authenticate by default.
  - [ ] everything is graphql? Including events? not sure.
       Maybe only applies to R not C.
  - [ ] support for SAGAs?

## Architecture ideas

### Common Core

This is code that is included which each module / service

  - [ ] access to eventsourcing
  - [ ] access to internal GQL client
  - [ ] extendability of web server
  - [ ] extendability of graphql schema
  - [ ] scheduling, cron & background tasks


## Questions

  - [ ] Have domain entities be pydantic models
  - [ ] setting management with fastapi dependency and pydantic .env files
  - [ ] eventsourcing & alembic?
  - [ ] scoped_session: What should the scope be when not in a request?
  - [ ] useful for es ? https://github.com/django/asgiref#function-wrappers
  - [ ] es: I don't like that changes are immediately published. It is not
        explicit for the user when setting an attribute it affects stuff
        in another request.

## TODO
  - [ ] https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/ asyn-exit-stack async-generator backports.
  - [ ] Use fastAPI sub applications to separate "modules", expect some boiler plate and having to figure out how to share dependencies.
  - [ ] Add celery queue, and FastAPI background tasks, both with eventsourcing. scoped session.
  - [ ] https://docs.authlib.org/en/latest/client/fastapi.html

## Problems with eventsourcing and fastapi

> In general you want one, and only one, instance of your application class in each process.

- Wasn't super clear if application was threadsafe
- Not clear how updating the domain models ends up storing events in the application's event store.
  turns out: the application has a persistence policy that subscribes to domain events. (using subscribe, which is the interface)
    This is magic. It should be simple, not magic (which is obscure)
- encryption is done after compression, that's not recommended!
- eventsourcing.utils.times.datetime_from_timestamp is naive. WTF.

- eventsourcing doesn't use asyncio
- eventsourcing doesn't use pedantic and lacks typing / ide support

## Considerations for the future


TODO: developer contention on the Commnds process?
if this is a single entry point how to deal with
 - code activity (development contention)
   there is no logic, it should be declarative from
   the dev teams and serve as a registry.
   MUCH like the schema first graphql,
   There might be something with FEDERATION
 - scale / distribution
   if this is just firing messages not doing logici,
   simply reccording the command it's FINE.
