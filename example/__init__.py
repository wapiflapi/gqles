from fastapi import FastAPI, Request, Response, Depends

import starlette_context
import starlette_context.middleware


import example.application


app = FastAPI()


class RequestHashPlugin(starlette_context.plugins.RequestIdPlugin):
    key = "__scope_uuid"

    def __init__(self):
        super().__init__(force_new_uuid=True, version=4)

    async def process_request(self, request: Request) -> str:
        value = await super().process_request(request)
        request.state.uuid = value
        return value

    async def enrich_response(self, response: Response) -> None:
         pass


app.add_middleware(
    starlette_context.middleware.ContextMiddleware, plugins=(
        RequestHashPlugin(),
        starlette_context.plugins.RequestIdPlugin(),
        starlette_context.plugins.CorrelationIdPlugin(),
    )
)


@app.on_event("startup")
async def setup_application():
    await example.application.init_application()


@app.on_event("shutdown")
async def teardown_application():
    await example.application.close_application()


@app.get("/")
async def root(
        application: example.application.Application = Depends(
            example.application.get_application),
):

    return dict(
        mission="Make it hard to mess up.",
        context=starlette_context.context,
        application=str(application),
    )
