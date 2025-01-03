
from pydantic import BaseModel, Field, field_validator

from typing import Annotated, List

class MonthlyWeatherProfileResponse(BaseModel):
    city: str
    month: int = Field(ge=1, le=12)
    min_temp_avg: Annotated[float, Field(ge=-50, le=50)] = Field(
        description="Average minimum temperature"
    )
    max_temp_avg: Annotated[float, Field(ge=-50, le=50)] = Field(
        description="Average maximum temperature"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "city": "London",
                    "month": 7,
                    "min_temp_avg": 15.5,
                    "max_temp_avg": 25.5,
                }
            ]
        }
    }


