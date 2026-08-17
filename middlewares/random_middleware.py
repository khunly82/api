import uuid

from fastapi import HTTPException, Request, Response
from redis import Redis
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware


class RandomMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, next):
        ip = request.client.host
        redis: Redis = request.app.state.redis
        await redis.set(f'{ip}:{uuid.uuid4()}', '', ex=60)
        count = 0
        async for _ in redis.scan_iter(match=f'{ip}:*'):
            count += 1
        if count >= 1000:
            return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        response = await next(request)
        return response