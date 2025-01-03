
from pydantic import BaseModel, Field, field_validator

from fastapi import FastAPI, Depends, HTTPException
from fastapi import Query

class BestTravelMonthFinderRequest(BaseModel):
    city: str = Field(..., description="Name of the city")
    min_temp: float = Field(
        ..., description="Minimum preferred temperature", ge=-50, le=50
    )
    max_temp: float = Field(
        ..., description="Maximum preferred temperature", ge=-50, le=50
    )

    @field_validator("city")
    @classmethod
    def city_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("city must not be empty")
        return value.strip()

    @classmethod
    async def validate_params(
        cls,
        city: str = Query(..., description="Name of the city"),
        min_temp: float = Query(
            ..., ge=-50, le=50, description="Minimum preferred temperature"
        ),
        max_temp: float = Query(
            ..., ge=-50, le=50, description="Maximum preferred temperature"
        ),
    ) -> "BestTravelMonthFinderRequest":
        if max_temp <= min_temp:
            raise HTTPException(
                status_code=422, detail="max_temp must be greater than min_temp"
            )
        return cls(city=city, min_temp=min_temp, max_temp=max_temp)


