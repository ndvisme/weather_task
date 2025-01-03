
from pydantic import BaseModel, Field, field_validator

from app.models.route_name import RouteName

from typing import Annotated, List

class RouteMetrics(BaseModel):
    route_name: RouteName
    hits: int = Field(ge=0)
    errors: int = Field(ge=0)
    avg_time: float = Field(ge=0)
    max_time: float = Field(ge=0)
    min_time: float = Field(ge=0)


class MetricsResponse(BaseModel):
    routes: List[RouteMetrics]


