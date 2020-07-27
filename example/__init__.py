from ariadne.asgi import GraphQL

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import starlette_context
import starlette_context.middleware

import sqlalchemy

import example.application
import example.database
import example.domain
import example.schema
import example.context


app = FastAPI()

app.mount("/graphql", GraphQL(
    example.schema.schema,
    debug=True,
))

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    starlette_context.middleware.ContextMiddleware, plugins=(
        example.context.RequestHashPlugin(),
        starlette_context.plugins.RequestIdPlugin(),
        starlette_context.plugins.CorrelationIdPlugin(),
    )
)


@app.on_event("startup")
async def setup_application():
    await example.application.init_system_runner()


@app.on_event("shutdown")
async def teardown_application():
    await example.application.close_system_runner()


@app.get("/")
async def root():

    aggregate = example.domain.CreateOrder.create()
    aggregate.__save__()

    return aggregate

    return dict(
        mission="Make it hard to mess up.",
        context=starlette_context.context,
    )


@app.get("/db")
async def db():

    insp = sqlalchemy.inspect(example.database.engine)

    return {
        table: {
            c["name"]: repr(c["type"]) for c in insp.get_columns(table)
        } for table in insp.get_table_names()
    }
