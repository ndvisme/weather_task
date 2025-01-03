from fastapi import FastAPI
from app.core.config import lifespan
from app.api.endpoints import weather, travel, metrics

app = FastAPI(lifespan=lifespan)

app.include_router(weather.router, prefix="/weather", tags=["weather"])
app.include_router(travel.router, prefix="/travel", tags=["travel"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
