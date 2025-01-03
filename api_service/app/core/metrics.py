from app.logger_config import logger

metrics_store = {
    "/weather/monthly-profile": {"hits": 0, "errors": 0, "times": []},
    "/travel/best-month": {"hits": 0, "errors": 0, "times": []},
    "/travel/compare-cities": {"hits": 0, "errors": 0, "times": []},
}

def update_metrics(route: str, duration: float, error: bool = False):
    if route in metrics_store:
        metrics_store[route]["hits"] += 1
        metrics_store[route]["times"].append(duration)
        if error:
            metrics_store[route]["errors"] += 1
        logger.info(
            f"Metrics updated for {route}: Duration={duration:.2f}s, Error={error}"
        )
