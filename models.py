"""
Pydantic Models for Weather Map API

Data models for validating and parsing weather data from API requests.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DailyUnits(BaseModel):
    """Units for daily weather measurements."""
    time: str = "iso8601"
    weather_code: str = "wmo code"
    temperature_2m_max: str = "°C"
    temperature_2m_min: str = "°C"
    precipitation_sum: str = "mm"
    wind_speed_10m_max: str = "km/h"
    cloud_cover_min: Optional[str] = "%"
    cloud_cover_max: Optional[str] = "%"


class DailyData(BaseModel):
    """Daily weather data arrays."""
    time: List[str]
    weather_code: List[int]
    temperature_2m_max: List[float]
    temperature_2m_min: List[float]
    precipitation_sum: List[float]
    wind_speed_10m_max: List[float]
    cloud_cover_min: Optional[List[int]] = None
    cloud_cover_max: Optional[List[int]] = None


class MeteoLocation(BaseModel):
    """Weather data for a specific location."""
    latitude: float
    longitude: float
    generationtime_ms: Optional[float] = None
    utc_offset_seconds: Optional[int] = 0
    timezone: Optional[str] = "GMT"
    timezone_abbreviation: Optional[str] = "GMT"
    elevation: Optional[float] = None
    daily_units: Optional[DailyUnits] = None
    daily: DailyData
    id: str
    capital: str = Field(..., description="Country code (e.g., 'dz' for Algeria)")
    name: str
    display_name: Optional[str] = None
    priority: Optional[int] = 1


class MeteoRequest(BaseModel):
    """Request body for generating a weather map."""
    meteo_data: List[MeteoLocation]
    title: Optional[str] = None
    day_index: Optional[int] = 0  # Which day to display (0 = first day)
