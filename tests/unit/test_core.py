"""Unit tests for core base classes."""

import pytest
from datetime import datetime, timezone
from typing import List

from little_big_data.core.base import DataPoint
from little_big_data.models.strava import StravaActivity, StravaAthlete


class TestDataPoint:
    """Test the DataPoint base class."""
    
    def test_create_data_point(self):
        """Test creating a basic data point."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        point = DataPoint(
            timestamp=timestamp,
            source="test",
            data_type="test_data",
            metadata={"key": "value"}
        )
        
        assert point.timestamp == timestamp
        assert point.source == "test"
        assert point.data_type == "test_data"
        assert point.metadata == {"key": "value"}
    
    def test_data_point_serialization(self):
        """Test that DataPoint can be serialized and deserialized."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        original = DataPoint(
            timestamp=timestamp,
            source="test",
            data_type="test_data",
            metadata={"id": 123, "value": 42.5}
        )
        
        # Serialize to dict
        data = original.model_dump()
        
        # Deserialize back
        restored = DataPoint.model_validate(data)
        
        assert restored.timestamp == original.timestamp
        assert restored.source == original.source
        assert restored.data_type == original.data_type
        assert restored.metadata == original.metadata
    
    def test_data_point_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        point = DataPoint(
            timestamp=datetime.now(timezone.utc),
            source="test",
            data_type="test"
        )
        
        assert point.metadata == {}


class TestStravaActivity:
    """Test the StravaActivity model."""
    
    def test_create_strava_activity(self):
        """Test creating a Strava activity."""
        timestamp = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        activity = StravaActivity(
            timestamp=timestamp,
            activity_id=12345,
            name="Morning Run",
            activity_type="Run",
            distance=5000.0,
            moving_time=1800,
            elapsed_time=1900,
            total_elevation_gain=50.0,
            average_speed=2.78,
            average_heartrate=150.0
        )
        
        assert activity.timestamp == timestamp
        assert activity.activity_id == 12345
        assert activity.name == "Morning Run"
        assert activity.activity_type == "Run"
        assert activity.distance == 5000.0
        assert activity.moving_time == 1800
        assert activity.elapsed_time == 1900
        assert activity.total_elevation_gain == 50.0
        assert activity.average_speed == 2.78
        assert activity.average_heartrate == 150.0
    
    def test_strava_activity_defaults(self):
        """Test that StravaActivity sets proper defaults."""
        activity = StravaActivity(
            timestamp=datetime.now(timezone.utc),
            activity_id=12345,
            name="Test Activity",
            activity_type="Run",
            distance=1000.0,
            moving_time=600,
            elapsed_time=700,
            total_elevation_gain=10.0
        )
        
        # Check DataPoint defaults are set
        assert activity.source == "strava"
        assert activity.data_type == "activity"
        
        # Check optional fields default to None
        assert activity.start_latlng is None
        assert activity.end_latlng is None
        assert activity.max_speed is None
        assert activity.max_heartrate is None
        assert activity.calories is None
        assert activity.description is None
    
    def test_strava_activity_with_optional_fields(self):
        """Test StravaActivity with all optional fields."""
        activity = StravaActivity(
            timestamp=datetime.now(timezone.utc),
            activity_id=12345,
            name="Complete Activity",
            activity_type="Ride",
            distance=25000.0,
            moving_time=3600,
            elapsed_time=3750,
            total_elevation_gain=200.0,
            start_latlng=(37.7749, -122.4194),
            end_latlng=(37.8049, -122.3894),
            average_speed=6.94,
            max_speed=15.0,
            average_heartrate=140.0,
            max_heartrate=160.0,
            calories=400.0,
            description="Great ride through the city!"
        )
        
        assert activity.start_latlng == (37.7749, -122.4194)
        assert activity.end_latlng == (37.8049, -122.3894)
        assert activity.max_speed == 15.0
        assert activity.max_heartrate == 160.0
        assert activity.calories == 400.0
        assert activity.description == "Great ride through the city!"
    
    def test_strava_activity_extra_fields(self):
        """Test that StravaActivity allows extra fields."""
        activity = StravaActivity(
            timestamp=datetime.now(timezone.utc),
            activity_id=12345,
            name="Test Activity",
            activity_type="Run",
            distance=1000.0,
            moving_time=600,
            elapsed_time=700,
            total_elevation_gain=10.0,
            extra_field="extra_value",
            another_field=123
        )
        
        # Extra fields should be accessible
        assert hasattr(activity, 'extra_field')
        assert hasattr(activity, 'another_field')


class TestStravaAthlete:
    """Test the StravaAthlete model."""
    
    def test_create_strava_athlete(self):
        """Test creating a Strava athlete."""
        athlete = StravaAthlete(
            id=123456,
            username="testuser",
            firstname="Test",
            lastname="User",
            city="Test City",
            state="Test State",
            country="Test Country",
            sex="M"
        )
        
        assert athlete.id == 123456
        assert athlete.username == "testuser"
        assert athlete.firstname == "Test"
        assert athlete.lastname == "User"
        assert athlete.city == "Test City"
        assert athlete.state == "Test State"
        assert athlete.country == "Test Country"
        assert athlete.sex == "M"
    
    def test_strava_athlete_minimal(self):
        """Test creating athlete with only required fields."""
        athlete = StravaAthlete(id=123456)
        
        assert athlete.id == 123456
        assert athlete.username is None
        assert athlete.firstname is None
        assert athlete.lastname is None
    
    def test_strava_athlete_with_dates(self):
        """Test athlete with datetime fields."""
        created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        athlete = StravaAthlete(
            id=123456,
            username="testuser",
            created_at=created_at,
            updated_at=updated_at,
            profile="https://example.com/profile.jpg"
        )
        
        assert athlete.created_at == created_at
        assert athlete.updated_at == updated_at
        assert athlete.profile == "https://example.com/profile.jpg" 