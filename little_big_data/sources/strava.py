"""Strava data source implementation."""

import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode

from ..core.base import DataSource, DataPoint
from ..models.strava import StravaActivity, StravaAthlete


class StravaSource(DataSource):
    """Strava API data source."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("strava", config)
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.access_token = config.get("access_token")
        self.refresh_token = config.get("refresh_token")
        self.base_url = "https://www.strava.com/api/v3"
        self._authenticated = False
    
    async def authenticate(self) -> bool:
        """Authenticate with Strava API."""
        if not self.access_token:
            raise ValueError("Access token is required for Strava authentication")
        
        # Test the token by fetching athlete info
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await client.get(f"{self.base_url}/athlete", headers=headers)
            
            if response.status_code == 200:
                self._authenticated = True
                return True
            elif response.status_code == 401:
                # Try to refresh the token if we have a refresh token
                if self.refresh_token:
                    return await self._refresh_access_token()
                else:
                    self._authenticated = False
                    return False
            else:
                self._authenticated = False
                return False
    
    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token"
            }
            
            response = await client.post("https://www.strava.com/oauth/token", data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.refresh_token = token_data["refresh_token"]
                self._authenticated = True
                return True
            else:
                self._authenticated = False
                return False
    
    async def fetch_data(self, start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> List[DataPoint]:
        """Fetch activities from Strava API."""
        if not self._authenticated:
            if not await self.authenticate():
                raise RuntimeError("Failed to authenticate with Strava")
        
        activities = []
        page = 1
        per_page = 200  # Max allowed by Strava
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            while True:
                params = {
                    "page": page,
                    "per_page": per_page
                }
                
                # Add date filters if provided
                if start_date:
                    params["after"] = int(start_date.timestamp())
                if end_date:
                    params["before"] = int(end_date.timestamp())
                
                response = await client.get(
                    f"{self.base_url}/athlete/activities",
                    headers=headers,
                    params=params
                )
                
                if response.status_code != 200:
                    break
                
                page_activities = response.json()
                
                if not page_activities:
                    break
                
                for activity_data in page_activities:
                    activity = self._convert_to_activity(activity_data)
                    activities.append(activity)
                
                # If we got fewer than per_page results, we're done
                if len(page_activities) < per_page:
                    break
                
                page += 1
        
        return activities
    
    def _convert_to_activity(self, data: Dict[str, Any]) -> StravaActivity:
        """Convert Strava API response to StravaActivity."""
        # Parse the start date
        start_date = datetime.fromisoformat(
            data["start_date_local"].replace("Z", "+00:00")
        )
        
        return StravaActivity(
            timestamp=start_date,
            activity_id=data["id"],
            name=data["name"],
            activity_type=data["type"],
            distance=data.get("distance", 0.0),
            moving_time=data.get("moving_time", 0),
            elapsed_time=data.get("elapsed_time", 0),
            total_elevation_gain=data.get("total_elevation_gain", 0.0),
            start_latlng=data.get("start_latlng"),
            end_latlng=data.get("end_latlng"),
            average_speed=data.get("average_speed"),
            max_speed=data.get("max_speed"),
            average_heartrate=data.get("average_heartrate"),
            max_heartrate=data.get("max_heartrate"),
            calories=data.get("calories"),
            description=data.get("description"),
            metadata={
                "id": data["id"],
                "raw_data": data  # Store original data for debugging
            }
        )
    
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types."""
        return ["activity"]
    
    @classmethod
    def get_authorization_url(cls, client_id: str, redirect_uri: str, 
                            scope: str = "read,activity:read_all") -> str:
        """Get the Strava OAuth authorization URL."""
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "approval_prompt": "force"
        }
        return f"https://www.strava.com/oauth/authorize?{urlencode(params)}"
    
    @classmethod
    async def exchange_code_for_token(cls, client_id: str, client_secret: str, 
                                    code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code"
            }
            
            response = await client.post("https://www.strava.com/oauth/token", data=data)
            response.raise_for_status()
            return response.json() 