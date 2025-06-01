"""Strava-specific data models."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from ..core.base import DataPoint


class StravaActivity(DataPoint):
    """Strava activity data point."""
    
    activity_id: int
    name: str
    activity_type: str  # Run, Ride, Swim, etc.
    distance: float  # meters
    moving_time: int  # seconds
    elapsed_time: int  # seconds
    total_elevation_gain: float  # meters
    start_latlng: Optional[tuple[float, float]] = None
    end_latlng: Optional[tuple[float, float]] = None
    average_speed: Optional[float] = None  # m/s
    max_speed: Optional[float] = None  # m/s
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    calories: Optional[float] = None
    description: Optional[str] = None
    
    model_config = {"extra": "allow"}
    
    def __init__(self, **data: Any):
        # Set the required DataPoint fields
        data.setdefault("source", "strava")
        data.setdefault("data_type", "activity")
        super().__init__(**data)


class StravaAthlete(BaseModel):
    """Strava athlete profile."""
    
    id: int
    username: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    sex: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    profile: Optional[str] = None  # Profile picture URL
    
    model_config = {"extra": "allow"} 