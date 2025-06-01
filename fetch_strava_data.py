#!/usr/bin/env python3
"""Quick script to fetch Strava data using the StravaSource class."""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from little_big_data.sources.strava import StravaSource


async def main():
    """Main function to fetch and display Strava data."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get Strava configuration from environment variables
    config = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "access_token": os.getenv("STRAVA_ACCESS_TOKEN"),
        "refresh_token": os.getenv("STRAVA_REFRESH_TOKEN"),
    }
    
    # Check if all required tokens are present
    missing_config = [key for key, value in config.items() if not value]
    if missing_config:
        print(f"Missing configuration: {', '.join(missing_config)}")
        print("Please check your .env file and ensure all Strava tokens are set.")
        return
    
    # Initialize Strava source
    strava_source = StravaSource(config)
    
    try:
        print("Authenticating with Strava...")
        authenticated = await strava_source.authenticate()
        
        if not authenticated:
            print("Failed to authenticate with Strava API")
            return
        
        print("✅ Successfully authenticated with Strava!")
        
        # Fetch activities from the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*10)
        
        print(f"Fetching activities from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        
        activities = await strava_source.fetch_data(start_date=start_date, end_date=end_date)
        
        print(f"\n📊 Found {len(activities)} activities:")
        print("-" * 80)
        
        if activities:
            print("Most recent activities:")
            for i, activity in enumerate(activities[:5]):  # Show first 5
                print(f"  {i+1}. {activity.name} - {activity.timestamp.strftime('%Y-%m-%d')} - {activity.activity_type}")
        
        # Display activity summary
        total_distance = 0
        total_time = 0
        activity_types = {}
        
        for activity in activities:
            print(f"🏃 {activity.name}")
            print(f"   Type: {activity.activity_type}")
            print(f"   Date: {activity.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Distance: {activity.distance / 1000:.2f} km")
            print(f"   Duration: {activity.moving_time // 60:.0f} minutes")
            if activity.average_speed:
                print(f"   Avg Speed: {activity.average_speed * 3.6:.2f} km/h")
            if activity.calories:
                print(f"   Calories: {activity.calories}")
            print()
            
            # Update totals
            total_distance += activity.distance
            total_time += activity.moving_time
            activity_types[activity.activity_type] = activity_types.get(activity.activity_type, 0) + 1
        
        # Display summary statistics
        print("=" * 80)
        print("📈 SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total Distance: {total_distance / 1000:.2f} km")
        print(f"Total Time: {total_time // 3600:.0f} hours {(total_time % 3600) // 60:.0f} minutes")
        print(f"Average Speed: {(total_distance / total_time) * 3.6:.2f} km/h" if total_time > 0 else "N/A")
        print("\nActivity Types:")
        for activity_type, count in activity_types.items():
            print(f"  {activity_type}: {count}")
        
    except Exception as e:
        print(f"❌ Error fetching Strava data: {e}")


if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  .env file not found!")
        print("Please create a .env file based on config.env.example with your Strava tokens.")
        print("You can copy the example file:")
        print("  cp config.env.example .env")
        print("Then edit .env with your actual Strava API credentials.")
    else:
        asyncio.run(main()) 