
from pydantic import BaseModel, Field, field_validator

from typing import Annotated, List

class BestTravelMonthResponse(BaseModel):
    city: str
    best_month: int = Field(ge=1, le=12)
    min_temp_diff: Annotated[float, Field(ge=0)] = Field(
        description="Difference between preferred and actual minimum temperature"
    )
    max_temp_diff: Annotated[float, Field(ge=0)] = Field(
        description="Difference between preferred and actual maximum temperature"
    )
    overall_diff: Annotated[float, Field(ge=0)] = Field(
        description="Sum of min_temp_diff and max_temp_diff"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "city": "London",
                    "best_month": 7,
                    "min_temp_diff": 2.50,
                    "max_temp_diff": 1.50,
                    "overall_diff": 4.00,
                }
            ]
        }
    }


