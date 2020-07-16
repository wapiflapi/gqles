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

## TODO
  - [ ] https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/ asyn-exit-stack async-generator backports.
  - [ ] Use fastAPI sub applications to separate "modules", expect some boiler plate and having to figure out how to share dependencies.

## Problems with eventsourcing and fastaip

> In general you want one, and only one, instance of your application class in each process.

- Wasn't super clear if application was threadsafe
