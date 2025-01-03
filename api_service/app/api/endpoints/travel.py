import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache
import time
from app.models.responses.best_travel_month import BestTravelMonthResponse
from app.models.requests.best_travel_month import BestTravelMonthFinderRequest
from app.models.responses.city_weather_comparison import CityWeatherComparisonResponse
from app.models.requests.city_weather_comparison import CityWeatherComparisonRequest
from app.services.queue_service import queue
from app.core.metrics import update_metrics
from app.logger_config import logger

router = APIRouter()


@router.get("/best-month", response_model=BestTravelMonthResponse)
@cache(expire=300)
async def get_best_travel_month(
    request: BestTravelMonthFinderRequest = Depends(
        BestTravelMonthFinderRequest.validate_params
    ),
):
    start_time = time.time()
    logger.info(f"Processing best travel month request for city: {request.city}")
    try:
        job = queue.enqueue(
            "worker.find_best_month", 
            request.city, 
            request.min_temp, 
            request.max_temp,
            job_timeout='5m'  # Add timeout
        )
        logger.info(f"Job enqueued with ID: {job.id}")

        while not job.is_finished and not job.is_failed:
            job.refresh()
            await asyncio.sleep(0.1)  # Prevent tight loop

        if job.is_failed:
            error_message = job.exc_info or "Job failed without specific error message"
            logger.error(f"Job failed: {error_message}")
            raise HTTPException(status_code=500, detail=error_message)

        result = job.result
        if result is None:
            raise HTTPException(status_code=500, detail="Job completed but returned no result")

        duration = time.time() - start_time
        update_metrics("/travel/best-month", duration)
        logger.info(f"Request completed successfully in {duration:.2f}s: {result}")

        return result
    except Exception as e:
        duration = time.time() - start_time
        update_metrics("/travel/best-month", duration, error=True)
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare-cities", response_model=CityWeatherComparisonResponse)
@cache(expire=300)
async def compare_cities(
    request: CityWeatherComparisonRequest = Depends(
        CityWeatherComparisonRequest.validate_params
    ),
):
    start_time = time.time()
    try:
        job = queue.enqueue("worker.compare_cities", request.cities, request.month)
        max_retries = 3
        retry_count = 0
        
        while not job.is_finished:
            job.refresh()
            if job.is_failed:
                if retry_count < max_retries:
                    retry_count += 1
                    job.requeue()
                    continue
                error_message = job.exc_info.strip() if job.exc_info else "Unknown error occurred"
                duration = time.time() - start_time
                update_metrics("/travel/compare-cities", duration, error=True)
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": error_message,
                        "retry_count": retry_count,
                        "job_id": job.id
                    }
                )

        duration = time.time() - start_time
        update_metrics("/travel/compare-cities", duration)
        return job.result

    except Exception as e:
        duration = time.time() - start_time
        update_metrics("/travel/compare-cities", duration, error=True)
        raise HTTPException(
            status_code=500, 
            detail=str(e)
        )
