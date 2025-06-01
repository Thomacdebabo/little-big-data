"""Unit tests for data sources."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import httpx
from urllib.parse import unquote

from little_big_data.sources.strava import StravaSource
from little_big_data.models.strava import StravaActivity


class TestStravaSource:
    """Test the StravaSource implementation."""
    
    def test_init(self):
        """Test StravaSource initialization."""
        config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token"
        }
        
        source = StravaSource(config)
        
        assert source.name == "strava"
        assert source.client_id == "test_client_id"
        assert source.client_secret == "test_client_secret"
        assert source.access_token == "test_access_token"
        assert source.refresh_token == "test_refresh_token"
        assert source.base_url == "https://www.strava.com/api/v3"
        assert not source._authenticated
    
    def test_get_supported_data_types(self):
        """Test getting supported data types."""
        source = StravaSource({"access_token": "test_token"})
        data_types = source.get_supported_data_types()
        
        assert data_types == ["activity"]
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, mock_strava_api_responses):
        """Test successful authentication."""
        source = StravaSource({"access_token": "valid_token"})
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_strava_api_responses["athlete"]
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await source.authenticate()
            
            assert result is True
            assert source._authenticated is True
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self):
        """Test authentication failure."""
        source = StravaSource({"access_token": "invalid_token"})
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await source.authenticate()
            
            assert result is False
            assert source._authenticated is False
    
    @pytest.mark.asyncio
    async def test_authenticate_no_token(self):
        """Test authentication without access token."""
        source = StravaSource({})
        
        with pytest.raises(ValueError, match="Access token is required"):
            await source.authenticate()
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, mock_strava_api_responses):
        """Test successful token refresh."""
        source = StravaSource({
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "refresh_token": "test_refresh_token"
        })
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_strava_api_responses["token_response"]
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await source._refresh_access_token()
            
            assert result is True
            assert source.access_token == "new_access_token"
            assert source.refresh_token == "new_refresh_token"
            assert source._authenticated is True
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_failure(self):
        """Test failed token refresh."""
        source = StravaSource({
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "refresh_token": "test_refresh_token"
        })
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await source._refresh_access_token()
            
            assert result is False
            assert source._authenticated is False
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_missing_credentials(self):
        """Test token refresh with missing credentials."""
        source = StravaSource({"refresh_token": "test_refresh_token"})
        
        result = await source._refresh_access_token()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_fetch_data_success(self, mock_strava_api_responses):
        """Test successful data fetching."""
        source = StravaSource({"access_token": "valid_token"})
        source._authenticated = True
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_strava_api_responses["activities"]
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            activities = await source.fetch_data()
            
            assert len(activities) == 2
            assert all(isinstance(activity, StravaActivity) for activity in activities)
            assert activities[0].activity_id == 12345
            assert activities[0].name == "Morning Run"
            assert activities[0].activity_type == "Run"
            assert activities[1].activity_id == 12346
            assert activities[1].name == "Evening Ride"
            assert activities[1].activity_type == "Ride"
    
    @pytest.mark.asyncio
    async def test_fetch_data_with_date_filters(self, mock_strava_api_responses):
        """Test fetching data with date filters."""
        source = StravaSource({"access_token": "valid_token"})
        source._authenticated = True
        
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_strava_api_responses["activities"]
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            activities = await source.fetch_data(start_date=start_date, end_date=end_date)
            
            # Verify the request was made with correct parameters
            mock_get = mock_client.return_value.__aenter__.return_value.get
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            
            assert "after" in params
            assert "before" in params
            assert params["after"] == int(start_date.timestamp())
            assert params["before"] == int(end_date.timestamp())
    
    @pytest.mark.asyncio
    async def test_fetch_data_not_authenticated(self):
        """Test fetching data when not authenticated."""
        source = StravaSource({"access_token": "invalid_token"})
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(RuntimeError, match="Failed to authenticate"):
                await source.fetch_data()
    
    @pytest.mark.asyncio
    async def test_fetch_data_pagination(self, mock_strava_api_responses):
        """Test data fetching with pagination."""
        source = StravaSource({"access_token": "valid_token"})
        source._authenticated = True
        
        # First page returns activities, second page returns empty
        responses = [
            mock_strava_api_responses["activities"],
            []
        ]
        
        with patch("httpx.AsyncClient") as mock_client:
            # Create separate mock responses for each call
            mock_responses = []
            for response_data in responses:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = response_data
                mock_responses.append(mock_response)
            
            # Mock get to return different responses on successive calls
            mock_client.return_value.__aenter__.return_value.get.side_effect = mock_responses
            
            activities = await source.fetch_data()
            
            # Should have made two requests (pagination)
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 2
            assert len(activities) == 2
    
    def test_convert_to_activity(self, mock_strava_api_responses):
        """Test converting API response to StravaActivity."""
        source = StravaSource({"access_token": "test_token"})
        api_data = mock_strava_api_responses["activities"][0]
        
        activity = source._convert_to_activity(api_data)
        
        assert isinstance(activity, StravaActivity)
        assert activity.activity_id == 12345
        assert activity.name == "Morning Run"
        assert activity.activity_type == "Run"
        assert activity.distance == 5000.0
        assert activity.moving_time == 1800
        assert activity.elapsed_time == 1900
        assert activity.total_elevation_gain == 50.0
        assert activity.start_latlng == (37.7749, -122.4194)
        assert activity.end_latlng == (37.7849, -122.4094)
        assert activity.average_speed == 2.78
        assert activity.max_speed == 4.5
        assert activity.average_heartrate == 150.0
        assert activity.max_heartrate == 165.0
        assert activity.calories == 250.0
        assert activity.description == "Great morning run!"
        assert activity.source == "strava"
        assert activity.data_type == "activity"
        assert activity.metadata["id"] == 12345
        assert "raw_data" in activity.metadata
    
    def test_convert_to_activity_minimal_data(self):
        """Test converting API response with minimal data."""
        source = StravaSource({"access_token": "test_token"})
        
        minimal_data = {
            "id": 99999,
            "name": "Minimal Activity",
            "type": "Workout",
            "start_date_local": "2024-01-01T10:00:00Z"
        }
        
        activity = source._convert_to_activity(minimal_data)
        
        assert activity.activity_id == 99999
        assert activity.name == "Minimal Activity"
        assert activity.activity_type == "Workout"
        assert activity.distance == 0.0  # Default value
        assert activity.moving_time == 0  # Default value
        assert activity.average_speed is None  # Not provided
    
    def test_get_authorization_url(self):
        """Test generating OAuth authorization URL."""
        client_id = "test_client_id"
        redirect_uri = "http://localhost:8000/callback"
        
        auth_url = StravaSource.get_authorization_url(client_id, redirect_uri)
        
        assert "https://www.strava.com/oauth/authorize" in auth_url
        assert f"client_id={client_id}" in auth_url
        assert "redirect_uri=" in auth_url
        assert unquote(auth_url).find(redirect_uri) != -1
        assert "response_type=code" in auth_url
        assert "scope=read%2Cactivity%3Aread_all" in auth_url or "scope=read,activity:read_all" in unquote(auth_url)
    
    def test_get_authorization_url_custom_scope(self):
        """Test generating OAuth URL with custom scope."""
        client_id = "test_client_id"
        redirect_uri = "http://localhost:8000/callback"
        custom_scope = "read,activity:read"
        
        auth_url = StravaSource.get_authorization_url(
            client_id, redirect_uri, scope=custom_scope
        )
        
        assert "scope=" in auth_url
        decoded_url = unquote(auth_url)
        assert custom_scope in decoded_url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, mock_strava_api_responses):
        """Test successful code exchange for token."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_strava_api_responses["token_response"]
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            token_data = await StravaSource.exchange_code_for_token(
                "test_client_id",
                "test_client_secret",
                "test_code"
            )
            
            assert token_data == mock_strava_api_responses["token_response"]
            
            # Verify the request was made correctly
            mock_post = mock_client.return_value.__aenter__.return_value.post
            call_args = mock_post.call_args
            data = call_args[1]["data"]
            
            assert data["client_id"] == "test_client_id"
            assert data["client_secret"] == "test_client_secret"
            assert data["code"] == "test_code"
            assert data["grant_type"] == "authorization_code"
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self):
        """Test failed code exchange for token."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Bad Request", request=MagicMock(), response=mock_response
            )
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(httpx.HTTPStatusError):
                await StravaSource.exchange_code_for_token(
                    "test_client_id",
                    "test_client_secret",
                    "invalid_code"
                ) 