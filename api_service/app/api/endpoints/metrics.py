from fastapi import APIRouter
from app.core.metrics import metrics_store
from app.logger_config import logger

router = APIRouter()

@router.get("")
async def get_metrics():
    logger.info("Retrieving metrics")
    return {
        "routes": {
            route: {
                "route_name": route,
                "hits": data["hits"],
                "errors": data["errors"],
                "avg_time": (
                    round(sum(data["times"]) / len(data["times"]), 2)
                    if data["times"]
                    else 0
                ),
                "max_time": round(max(data["times"]), 2) if data["times"] else 0,
                "min_time": round(min(data["times"]), 2) if data["times"] else 0,
            }
            for route, data in metrics_store.items()
        }
    }
