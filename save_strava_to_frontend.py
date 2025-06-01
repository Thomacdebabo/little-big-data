#!/usr/bin/env python3
"""Script to fetch Strava data and save it to the frontend storage."""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv


async def save_strava_data():
    """Fetch Strava data and save it to the frontend storage."""
    load_dotenv()
    
    # Get tokens from .env
    access_token = os.getenv("STRAVA_ACCESS_TOKEN")
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
    
    if not access_token:
        print("❌ No access token found in .env file")
        return
    
    # Prepare request data
    payload = {
        "access_token": access_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "days_back": 365*10  # Get a full year of data
    }
    
    print("🔄 Fetching Strava data and saving to frontend storage...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/data/strava/fetch",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"📊 {result['message']}")
                
                # Now check the data summary
                summary_response = await client.get("http://localhost:8000/data/summary")
                if summary_response.status_code == 200:
                    summary = summary_response.json()
                    print(f"\n📈 Total data points: {summary['total_points']}")
                    print(f"🏃 Sources: {list(summary['sources'].keys())}")
                
                print("\n🎉 Your Strava data is now available in the frontend!")
                print("🌐 Visit these URLs to see your data:")
                print("   • Timeline: http://localhost:8000/visualizations/timeline?source=strava")
                print("   • Dashboard: http://localhost:8000/visualizations/dashboard?source=strava")
                print("   • Heatmap: http://localhost:8000/visualizations/heatmap?source=strava")
                print("   • Weekly Running Stats: http://localhost:8000/visualizations/weekly-running-stats?source=strava")
                print("   • Data browser: http://localhost:8000/data?source=strava")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(save_strava_data()) 