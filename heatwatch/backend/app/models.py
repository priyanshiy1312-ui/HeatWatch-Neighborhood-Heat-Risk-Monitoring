"""Pydantic schemas for ward inputs and weather."""
from pydantic import BaseModel, Field


class WardInputs(BaseModel):
    id: str
    name: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    population: int = Field(ge=0)
    pop_density: float = Field(ge=0, description="people per km2")
    green_cover: float = Field(ge=0, le=1)
    built_up: float = Field(ge=0, le=1)
    lst_anomaly_c: float = Field(description="land surface temp minus city mean, deg C")
    vulnerable_share: float = Field(ge=0, le=1)
    water_points: int = Field(ge=0)
    nearest_water_m: float = Field(ge=0)
    data_quality: str = "sample"


class DayWeather(BaseModel):
    date: str
    temp_c: float
    humidity_pct: float = Field(ge=0, le=100)
