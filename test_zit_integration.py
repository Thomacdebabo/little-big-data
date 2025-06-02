#!/usr/bin/env python3
"""Test script for zit integration."""

import asyncio
from datetime import datetime, timedelta
from little_big_data.sources import ZitSource


async def test_zit_integration():
    """Test the zit integration."""
    print("Testing Zit integration...")
    
    # Create zit source
    zit_source = ZitSource()
    
    # Test authentication (check if .zit directory exists)
    authenticated = await zit_source.authenticate()
    print(f"Authentication: {'✓' if authenticated else '✗'}")
    
    if not authenticated:
        print("No zit data directory found. Make sure you have used zit to track time.")
        return
    
    # Get available dates
    dates = zit_source.get_available_dates()
    print(f"Available dates: {dates[:5]}...")  # Show first 5 dates
    
    # Get current task
    current_task = await zit_source.get_current_task()
    print(f"Current task: {current_task}")
    
    # Fetch recent data (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"Fetching data from {start_date.date()} to {end_date.date()}...")
    data_points = await zit_source.fetch_data(start_date, end_date)
    
    print(f"Found {len(data_points)} data points")
    
    # Show some sample data
    if data_points:
        print("\nSample data points:")
        for i, dp in enumerate(data_points[:5]):  # Show first 5
            print(f"  {i+1}. {dp.timestamp} - {dp.data_type}: {dp.metadata.get('project_name', 'Unknown')}")
            if dp.data_type == "subtask" and dp.metadata.get('note'):
                print(f"     Note: {dp.metadata['note']}")
    
    # Get daily summary for today
    today_summary = await zit_source.get_daily_summary()
    print(f"\nToday's summary:")
    print(f"  Total projects: {today_summary['total_projects']}")
    print(f"  Total events: {today_summary['total_events']}")
    print(f"  Projects: {today_summary['projects']}")
    
    if today_summary['project_times']:
        print("  Time spent:")
        for project, seconds in today_summary['project_times'].items():
            hours = seconds / 3600
            print(f"    {project}: {hours:.1f} hours")

if __name__ == "__main__":
    asyncio.run(test_zit_integration()) 