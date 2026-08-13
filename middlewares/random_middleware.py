from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RandomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, next):
        print('-------------BEFORE----------')
        print(request.client.host)
        response = await next(request)
        print('-------------AFTER----------------')
        return response