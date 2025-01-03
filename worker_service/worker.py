import httpx
import statistics
from redis import Redis, ConnectionPool
from rq import Worker
import json
import time
from concurrent.futures import ThreadPoolExecutor
import zlib
from datetime import datetime

from logger import setup_logger

logger = setup_logger("worker")

REDIS_POOL = ConnectionPool(host='redis', max_connections=10)
redis_conn = Redis(connection_pool=REDIS_POOL)

# By popularity & size
TOP_CITIES = [
#    "Tokyo", "Delhi", "Shanghai", "São Paulo", 
#    "Mexico City", "Cairo", "Mumbai", "Beijing",
    "New York", "London"
]

# This data doesn't change. Let the cache live
CACHE_EXPIRY = 86400 * 7  # 7 days
MAX_WORKERS = 4
API_RATE_LIMIT = 0.5

class WeatherAPI:
    def __init__(self):
        self.client = httpx.Client(
            timeout=30,
            limits=httpx.Limits(max_keepalive_connections=5),
            headers={'Accept-Encoding': 'gzip'}
        )
        self.last_call = 0

    def _rate_limit(self):
        now = time.time()
        time_since_last = now - self.last_call
        if time_since_last < API_RATE_LIMIT:
            time.sleep(API_RATE_LIMIT - time_since_last)
        self.last_call = time.time()

    def get_weather_data(self, city: str, start_date: str, end_date: str):
        self._rate_limit()
        logger.info(f"Fetching weather data for {city} from {start_date} to {end_date}")
        try:
            # Get coordinates
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
            geo_response = self.client.get(geocoding_url)
            geo_data = geo_response.json()

            if "results" not in geo_data or not geo_data["results"]:
                logger.error(f"No coordinates found for city: {city}")
                raise ValueError(f"Invalid city name or city not found: {city}")

            location = geo_data["results"][0]

            self._rate_limit()
            # Get weather data
            weather_url = (
                f"https://archive-api.open-meteo.com/v1/archive"
                f"?latitude={location['latitude']}"
                f"&longitude={location['longitude']}"
                f"&start_date={start_date}"
                f"&end_date={end_date}"
                f"&daily=temperature_2m_max,temperature_2m_min"
            )
            weather_response = self.client.get(weather_url)
            weather_data = weather_response.json()

            if "error" in weather_data:
                raise ValueError(f"Weather API error: {weather_data['error']}")

            return weather_data
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while fetching weather data: {str(e)}")
            raise ValueError(f"Failed to fetch weather data: {str(e)}")
        except KeyError as e:
            logger.error(f"Unexpected API response format: {str(e)}")
            raise ValueError(f"Invalid API response format: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            raise
def compress_data(data: dict) -> bytes:
    return zlib.compress(json.dumps(data).encode())

def decompress_data(compressed_data: bytes) -> dict:
    return json.loads(zlib.decompress(compressed_data).decode())

def cache_key(city: str, month: int) -> str:
    return f"weather:{city.lower()}:{month}"

def get_cached_profile(city: str, month: int):
    key = cache_key(city, month)
    cached = redis_conn.get(key)
    return decompress_data(cached) if cached else None

def cache_profile(city: str, month: int, data: dict):
    key = cache_key(city, month)
    compressed_data = compress_data(data)
    redis_conn.setex(key, CACHE_EXPIRY, compressed_data)

def cache_city_month(city: str, month: int):
    try:
        if not get_cached_profile(city, month):
            profile = get_monthly_profile(city, month)
            cache_profile(city, month, profile)
            logger.info(f"Cached data for {city} - Month {month}")
    except Exception as e:
        logger.error(f"Failed to cache {city} month {month}: {str(e)}")

def initialize_cache():
    logger.info("Starting parallel cache initialization")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for city in TOP_CITIES:
            for month in range(1, 13):
                futures.append(
                    executor.submit(cache_city_month, city, month)
                )
        
        # Wait for all tasks to complete
        for future in futures:
            future.result()
    
    duration = time.time() - start_time
    logger.info(f"Cache initialization completed in {duration:.2f} seconds")

def get_monthly_profile(city: str, month: int):
    cached = get_cached_profile(city, month)
    if cached:
        logger.info(f"Cache hit for {city}, month {month}")
        return cached
        
    logger.info(f"Cache miss for {city}, month {month}")
    weather_api = WeatherAPI()
    
    # Validate city first with a single API call
    try:
        logger.info(f"Validating city {city}")
        test_data = weather_api.get_weather_data(
            city, 
            f"2023-{month:02d}-01", 
            f"2023-{month:02d}-28"
        )
        # Store first month's data to avoid duplicate API call
        all_temps = {
            "min": test_data["daily"]["temperature_2m_min"],
            "max": test_data["daily"]["temperature_2m_max"]
        }
    except ValueError as e:
        logger.error(f"Invalid city {city}: {str(e)}")
        raise ValueError(f"City not found: {city}")

    # Only proceed with historical data if city is valid
    try:
        for year in range(2018, 2023):  # Skip 2023 since we already have it
            logger.info(f"Fetching data for {city}, year {year}, month {month}")
            data = weather_api.get_weather_data(
                city,
                f"{year}-{month:02d}-01",
                f"{year}-{month:02d}-28"
            )
            all_temps["min"].extend(data["daily"]["temperature_2m_min"])
            all_temps["max"].extend(data["daily"]["temperature_2m_max"])

        result = {
            "city": city,
            "month": month,
            "min_temp_avg": round(statistics.mean(all_temps["min"]), 2),
            "max_temp_avg": round(statistics.mean(all_temps["max"]), 2),
            "updated_at": datetime.now().isoformat()
        }
        
        cache_profile(city, month, result)
        return result
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {city}: {str(e)}")
        raise ValueError(f"Failed to fetch weather data: {str(e)}")


def find_best_month(city: str, min_temp: float, max_temp: float):
    logger.info(f"Finding best month for {city} with temp range {min_temp}-{max_temp}")
    try:
        best_month_data = {"overall_diff": float("inf")}
        
        for month in range(1, 13):
            profile = get_monthly_profile(city, month)
            min_diff = abs(profile["min_temp_avg"] - min_temp)
            max_diff = abs(profile["max_temp_avg"] - max_temp)
            overall_diff = min_diff + max_diff
            
            if overall_diff < best_month_data["overall_diff"]:
                best_month_data = {
                    "city": city,
                    "best_month": month,
                    "min_temp_diff": round(min_diff, 2),
                    "max_temp_diff": round(max_diff, 2),
                    "overall_diff": round(overall_diff, 2)
                }
        
        logger.info(f"Found best month for {city}: {best_month_data['best_month']}")
        return best_month_data
    except Exception as e:
        logger.error(f"Error in find_best_month: {str(e)}")
        raise

def compare_cities(cities: list, month: int):
    logger.info(f"Comparing cities: {cities} for month {month}")
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            profiles = list(executor.map(
                lambda city: get_monthly_profile(city.strip(), month),
                cities
            ))
        
        if not profiles:
            raise ValueError("No valid city profiles could be retrieved")
            
        # Restructure the response to match the model
        city_data = {
            profile["city"]: {
                "min_temp_avg": profile["min_temp_avg"],
                "max_temp_avg": profile["max_temp_avg"]
            }
            for profile in profiles
        }
        
        result = {
            "month": month,
            "cities": city_data  # Add the cities key to match the model
        }
        
        logger.info(f"Completed city comparison: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in compare_cities: {str(e)}")
        raise ValueError(f"Failed to compare cities: {str(e)}")

if __name__ == "__main__":
    logger.info("Worker starting up")
    initialize_cache()
    worker = Worker(["default"], connection=redis_conn)
    worker.work()
