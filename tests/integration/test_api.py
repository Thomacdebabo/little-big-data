"""Integration tests for API endpoints."""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from little_big_data.storage.json_storage import JsonStorage


class TestAPIEndpoints:
    """Test API endpoints integration."""
    
    def test_health_endpoint(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_home_page(self, api_client):
        """Test home page renders."""
        response = api_client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Little Big Data" in response.text
    
    def test_data_sources_endpoint(self, api_client):
        """Test data sources endpoint."""
        response = api_client.get("/data/sources")
        
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert len(data["sources"]) > 0
        
        # Check Strava source is listed
        strava_source = next(
            (s for s in data["sources"] if s["name"] == "strava"),
            None
        )
        assert strava_source is not None
        assert strava_source["description"] == "Strava fitness activities"
        assert "activity" in strava_source["data_types"]
    
    def test_data_summary_empty(self, api_client):
        """Test data summary with no data."""
        # Mock empty storage
        with patch("little_big_data.api.main.storage") as mock_storage:
            mock_storage.load.return_value = []
            
            response = api_client.get("/data/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_points"] == 0
            assert data["sources"] == {}
            assert data["date_range"] is None
    
    @pytest.mark.asyncio
    async def test_data_summary_with_data(self, api_client, sample_strava_activities, temp_dir):
        """Test data summary with actual data."""
        # Setup storage with test data
        storage = JsonStorage(base_path=str(temp_dir))
        await storage.save(sample_strava_activities)
        
        with patch("little_big_data.api.main.storage", storage):
            response = api_client.get("/data/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_points"] == 3
            assert "strava" in data["sources"]
            assert data["sources"]["strava"]["count"] == 3
            assert "activity" in data["sources"]["strava"]["data_types"]
            assert data["date_range"] is not None
    
    def test_get_data_empty(self, api_client):
        """Test getting data when storage is empty."""
        with patch("little_big_data.api.main.storage") as mock_storage:
            mock_storage.load.return_value = []
            
            response = api_client.get("/data")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0
            assert data["data"] == []
    
    @pytest.mark.asyncio
    async def test_get_data_with_filters(self, api_client, sample_strava_activities, temp_dir):
        """Test getting data with filters."""
        # Setup storage with test data
        storage = JsonStorage(base_path=str(temp_dir))
        await storage.save(sample_strava_activities)
        
        with patch("little_big_data.api.main.storage", storage):
            # Test source filter
            response = api_client.get("/data?source=strava")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 3
            
            # Test data type filter
            response = api_client.get("/data?data_type=activity")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 3
            
            # Test limit
            response = api_client.get("/data?limit=2")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
    
    def test_fetch_strava_data_missing_token(self, api_client):
        """Test fetching Strava data without access token."""
        response = api_client.post(
            "/data/strava/fetch",
            json={"days_back": 30}
        )
        
        # Should fail validation because access_token is required
        assert response.status_code == 422
    
    def test_fetch_strava_data_authentication_failure(self, api_client):
        """Test fetching Strava data with invalid token."""
        with patch("little_big_data.sources.strava.StravaSource") as mock_source_class:
            mock_source = MagicMock()
            mock_source.authenticate.return_value = False
            mock_source_class.return_value = mock_source
            
            response = api_client.post(
                "/data/strava/fetch",
                json={"access_token": "invalid_token"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "Failed to authenticate" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_fetch_strava_data_success(self, api_client, sample_strava_activities):
        """Test successful Strava data fetching."""
        with patch("little_big_data.sources.strava.StravaSource") as mock_source_class:
            mock_source = MagicMock()
            mock_source.authenticate.return_value = True
            mock_source.fetch_data.return_value = sample_strava_activities
            mock_source_class.return_value = mock_source
            
            with patch("little_big_data.api.main.storage") as mock_storage:
                mock_storage.save.return_value = None
                
                response = api_client.post(
                    "/data/strava/fetch",
                    json={"access_token": "valid_token", "days_back": 30}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["count"] == 3
                assert "Fetched and saved 3 activities" in data["message"]
                
                # Verify storage.save was called
                mock_storage.save.assert_called_once()
    
    def test_visualizations_timeline_empty_data(self, api_client):
        """Test timeline visualization with empty data."""
        with patch("little_big_data.api.main.storage") as mock_storage:
            mock_storage.load.return_value = []
            
            response = api_client.get("/visualizations/timeline")
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            assert "No data available" in response.text
    
    @pytest.mark.asyncio
    async def test_visualizations_timeline_with_data(self, api_client, sample_strava_activities, temp_dir):
        """Test timeline visualization with data."""
        storage = JsonStorage(base_path=str(temp_dir))
        await storage.save(sample_strava_activities)
        
        with patch("little_big_data.api.main.storage", storage):
            response = api_client.get("/visualizations/timeline")
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            assert "Activity Timeline" in response.text
            assert "plotly" in response.text.lower()
    
    def test_strava_auth_url(self, api_client):
        """Test getting Strava OAuth URL."""
        response = api_client.get("/auth/strava/url?client_id=test_client_id")
        
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "https://www.strava.com/oauth/authorize" in data["auth_url"]
        assert "client_id=test_client_id" in data["auth_url"] 