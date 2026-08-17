import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, staticfiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

import controllers
from middlewares.random_middleware import RandomMiddleware
from utils.application_utils import load_routers

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url(os.getenv('REDIS_HOST'))
    app.state.redis = redis
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield

# créer une instance de FastAPI
app = FastAPI(lifespan=lifespan)

app.mount('/public', staticfiles.StaticFiles(directory='static'))

app.add_middleware(RandomMiddleware)

# charger tous les router se trouvant dans controllers
load_routers(app, controllers)

if __name__ == '__main__':
    # exposer FastAPI sur le port 8000
    uvicorn.run(
        'server:app', 
        host='127.0.0.1',
        port=8000,
        reload=True
    )
