from fastapi import FastAPI
from redis import Redis
import statistics

app = FastAPI()
redis_conn = Redis(host='redis')

@app.get("/metrics")
async def get_metrics():
    metrics = {
        "/weather/monthly-profile": redis_conn.hgetall("metrics:monthly-profile"),
        "/travel/best-month": redis_conn.hgetall("metrics:best-month"),
        "/travel/compare-cities": redis_conn.hgetall("metrics:compare-cities")
    }
    
    return {
        "routes": {
            route: {
                "route_name": route,
                "hits": int(data.get(b"hits", 0)),
                "errors": int(data.get(b"errors", 0)),
                "avg_time": float(data.get(b"avg_time", 0)),
                "max_time": float(data.get(b"max_time", 0)),
                "min_time": float(data.get(b"min_time", 0))
            }
            for route, data in metrics.items()
        }
    }
