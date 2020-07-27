from fastapi import Request, Response

from starlette_context.plugins.plugin_uuid import PluginUUIDBase


class RequestHashPlugin(PluginUUIDBase):
    key = "__scope_uuid"

    def __init__(self):
        super().__init__(force_new_uuid=True, version=4)

    async def process_request(self, request: Request) -> str:
        value = await super().process_request(request)
        request.state.uuid = value
        return value

    async def enrich_response(self, response: Response) -> None:
        pass
