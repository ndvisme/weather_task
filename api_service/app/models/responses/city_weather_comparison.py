from typing import Dict, Annotated
from pydantic import BaseModel, Field, RootModel

class CityWeatherProfile(BaseModel):
    min_temp_avg: Annotated[float, Field(ge=-50, le=50)]
    max_temp_avg: Annotated[float, Field(ge=-50, le=50)]

class CityWeatherData(BaseModel):
    month: int = Field(ge=1, le=12)
    cities: Dict[str, CityWeatherProfile]

class CityWeatherComparisonResponse(RootModel):
    root: CityWeatherData

    @property
    def month(self) -> int:
        return self.root.month

    def model_dump(self, **kwargs):
        data = self.root.model_dump(**kwargs)
        return {
            "month": data["month"],
            **data["cities"]
        }
