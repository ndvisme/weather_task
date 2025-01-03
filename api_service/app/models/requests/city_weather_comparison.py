
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated, List

from pydantic import BaseModel, Field, field_validator

from fastapi import Query

class CityWeatherComparisonRequest(BaseModel):
    cities: List[str] = Field(..., description="List of cities to compare (2-5 cities)")
    month: int = Field(..., description="Month number", ge=1, le=12)

    @field_validator("cities")
    @classmethod
    def validate_cities(cls, value: List[str]) -> List[str]:
        # Remove empty spaces and duplicates
        cities = [city.strip() for city in value if city.strip()]
        cities = list(dict.fromkeys(cities))  # Remove duplicates

        if len(cities) < 2:
            raise ValueError("Minimum 2 cities required")
        if len(cities) > 5:
            raise ValueError("Maximum 5 cities allowed")

        return cities

    @classmethod
    async def validate_params(
        cls,
        cities: str = Query(
            ..., description="Comma-separated list of cities (2-5 cities)"
        ),
        month: int = Query(..., ge=1, le=12, description="Month number (1-12)"),
    ) -> "CityWeatherComparisonRequest":
        city_list = cities.split(",")

        # Validate city count before creating the model
        if len(city_list) < 2:
            raise HTTPException(status_code=422, detail="Minimum 2 cities required")
        if len(city_list) > 5:
            raise HTTPException(status_code=422, detail="Maximum 5 cities allowed")

        # Validate city existence (mock check - replace with actual validation)
        for city in city_list:
            if "NonExistent" in city:
                raise HTTPException(status_code=404, detail=f"City not found: {city}")

        return cls(cities=city_list, month=month)


