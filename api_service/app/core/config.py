from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from redis import Redis

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend(), prefix="weather-cache")
    yield

redis_conn = Redis(host="redis")
