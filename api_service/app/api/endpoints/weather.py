from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache
import time
from app.models.responses.monthly_weather_profile import MonthlyWeatherProfileResponse
from app.models.requests.monthly_weather_profile import MonthlyWeatherProfileRequest
from app.services.queue_service import queue
from app.core.metrics import update_metrics
from app.logger_config import logger

router = APIRouter()

@router.get("/monthly-profile", response_model=MonthlyWeatherProfileResponse)
@cache(expire=300)
async def get_monthly_profile(
    request: MonthlyWeatherProfileRequest = Depends(
        MonthlyWeatherProfileRequest.validate_params
    ),
):
    start_time = time.time()
    logger.info(
        f"Processing monthly profile request for city: {request.city}, month: {request.month}"
    )
    
    try:
        job = queue.enqueue("worker.get_monthly_profile", request.city, request.month)
        logger.info(f"Job enqueued with ID: {job.id}")
        
        max_retries = 3
        retry_count = 0
        
        while not job.is_finished:
            job.refresh()
            if job.is_failed:
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f"Retrying job {job.id}, attempt {retry_count}")
                    job.requeue()
                    continue
                    
                error_message = job.exc_info.strip() if job.exc_info else "Unknown error occurred"
                duration = time.time() - start_time
                update_metrics("/weather/monthly-profile", duration, error=True)
                logger.error(f"Job failed after {retry_count} retries: {error_message}")
                
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": error_message,
                        "retry_count": retry_count,
                        "job_id": job.id,
                        "city": request.city,
                        "month": request.month
                    }
                )

        duration = time.time() - start_time
        update_metrics("/weather/monthly-profile", duration)
        logger.info(f"Request completed successfully in {duration:.2f}s: {job.result}")
        return job.result
        
    except Exception as e:
        duration = time.time() - start_time
        update_metrics("/weather/monthly-profile", duration, error=True)
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
