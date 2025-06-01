"""Pytest configuration and shared fixtures."""

import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, AsyncGenerator

import pytest
from fastapi.testclient import TestClient

from little_big_data.core.base import DataPoint
from little_big_data.models.strava import StravaActivity
from little_big_data.storage.json_storage import JsonStorage
from little_big_data.api.main import app


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def json_storage(temp_dir):
    """Create a JsonStorage instance with temporary directory."""
    return JsonStorage(base_path=str(temp_dir))


@pytest.fixture
def sample_data_points() -> List[DataPoint]:
    """Create sample data points for testing."""
    return [
        DataPoint(
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            source="test_source",
            data_type="test_type",
            metadata={"id": "1", "value": 10}
        ),
        DataPoint(
            timestamp=datetime(2024, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
            source="test_source",
            data_type="test_type",
            metadata={"id": "2", "value": 20}
        ),
        DataPoint(
            timestamp=datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            source="another_source",
            data_type="another_type",
            metadata={"id": "3", "value": 30}
        ),
    ]


@pytest.fixture
def sample_strava_activities() -> List[StravaActivity]:
    """Create sample Strava activities for testing."""
    return [
        StravaActivity(
            timestamp=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
            activity_id=12345,
            name="Morning Run",
            activity_type="Run",
            distance=5000.0,  # 5km in meters
            moving_time=1800,  # 30 minutes
            elapsed_time=1900,
            total_elevation_gain=50.0,
            average_speed=2.78,  # ~10 km/h
            average_heartrate=150.0,
            metadata={"id": 12345}
        ),
        StravaActivity(
            timestamp=datetime(2024, 1, 2, 18, 0, 0, tzinfo=timezone.utc),
            activity_id=12346,
            name="Evening Ride",
            activity_type="Ride",
            distance=25000.0,  # 25km
            moving_time=3600,  # 1 hour
            elapsed_time=3750,
            total_elevation_gain=200.0,
            average_speed=6.94,  # 25 km/h
            max_speed=15.0,
            average_heartrate=140.0,
            calories=400.0,
            metadata={"id": 12346}
        ),
        StravaActivity(
            timestamp=datetime(2024, 1, 3, 7, 30, 0, tzinfo=timezone.utc),
            activity_id=12347,
            name="Pool Swim",
            activity_type="Swim",
            distance=1000.0,  # 1km
            moving_time=2400,  # 40 minutes
            elapsed_time=2700,
            total_elevation_gain=0.0,
            average_speed=0.42,
            metadata={"id": 12347}
        ),
    ]


@pytest.fixture
def api_client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_strava_api_responses():
    """Mock Strava API responses for testing."""
    return {
        "athlete": {
            "id": 123456,
            "username": "testuser",
            "firstname": "Test",
            "lastname": "User",
            "city": "Test City",
            "state": "Test State",
            "country": "Test Country",
            "sex": "M",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "profile": "https://example.com/profile.jpg"
        },
        "activities": [
            {
                "id": 12345,
                "name": "Morning Run",
                "type": "Run",
                "start_date_local": "2024-01-01T09:00:00Z",
                "distance": 5000.0,
                "moving_time": 1800,
                "elapsed_time": 1900,
                "total_elevation_gain": 50.0,
                "start_latlng": [37.7749, -122.4194],
                "end_latlng": [37.7849, -122.4094],
                "average_speed": 2.78,
                "max_speed": 4.5,
                "average_heartrate": 150.0,
                "max_heartrate": 165.0,
                "calories": 250.0,
                "description": "Great morning run!"
            },
            {
                "id": 12346,
                "name": "Evening Ride",
                "type": "Ride",
                "start_date_local": "2024-01-02T18:00:00Z",
                "distance": 25000.0,
                "moving_time": 3600,
                "elapsed_time": 3750,
                "total_elevation_gain": 200.0,
                "start_latlng": [37.7749, -122.4194],
                "end_latlng": [37.8049, -122.3894],
                "average_speed": 6.94,
                "max_speed": 15.0,
                "average_heartrate": 140.0,
                "max_heartrate": 160.0,
                "calories": 400.0,
                "description": None
            }
        ],
        "token_response": {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1735689600,
            "token_type": "Bearer"
        }
    } 