
from pydantic import BaseModel, Field, field_validator

from fastapi import Query

class MonthlyWeatherProfileRequest(BaseModel):
    city: str = Field(..., description="Name of the city")
    month: int = Field(..., description="Month number", ge=1, le=12)

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
        month: int = Query(..., ge=1, le=12, description="Month number (1-12)"),
    ) -> "MonthlyWeatherProfileRequest":
        return cls(city=city, month=month)


