#!/usr/bin/env python3
"""Command-line interface for Little Big Data."""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from little_big_data.storage.json_storage import JsonStorage
from little_big_data.sources.strava import StravaSource

app = typer.Typer(help="Little Big Data CLI")
console = Console()


@app.command()
def run():
    """Start the web server."""
    import uvicorn
    from little_big_data.api.main import app as web_app
    
    rprint("🚀 Starting Little Big Data server...")
    uvicorn.run(
        "little_big_data.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


@app.command()
def status():
    """Show data storage status."""
    async def _status():
        storage = JsonStorage()
        data_points = await storage.load()
        
        if not data_points:
            rprint("📊 No data stored yet")
            return
        
        # Create summary table
        table = Table(title="Data Summary")
        table.add_column("Source", style="cyan")
        table.add_column("Data Type", style="magenta")
        table.add_column("Count", style="green")
        table.add_column("Date Range", style="yellow")
        
        # Group by source and data type
        groups = {}
        for point in data_points:
            key = (point.source, point.data_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(point)
        
        for (source, data_type), points in groups.items():
            count = len(points)
            start_date = min(p.timestamp for p in points).date()
            end_date = max(p.timestamp for p in points).date()
            date_range = f"{start_date} to {end_date}"
            
            table.add_row(source, data_type, str(count), date_range)
        
        console.print(table)
        rprint(f"\n📈 Total data points: {len(data_points)}")
    
    asyncio.run(_status())


@app.command()
def fetch_strava(
    access_token: str = typer.Option(..., help="Strava access token"),
    days: int = typer.Option(30, help="Number of days to fetch"),
    save: bool = typer.Option(True, help="Save data to storage")
):
    """Fetch data from Strava API."""
    async def _fetch():
        config = {"access_token": access_token}
        strava = StravaSource(config)
        
        rprint("🔐 Authenticating with Strava...")
        if not await strava.authenticate():
            rprint("❌ Authentication failed")
            sys.exit(1)
        
        rprint(f"📡 Fetching last {days} days of activities...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        activities = await strava.fetch_data(start_date=start_date, end_date=end_date)
        rprint(f"✅ Fetched {len(activities)} activities")
        
        if save:
            rprint("💾 Saving to storage...")
            storage = JsonStorage()
            await storage.save(activities)
            rprint("✅ Data saved successfully")
        
        # Show summary
        if activities:
            table = Table(title="Fetched Activities")
            table.add_column("Date", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Type", style="magenta")
            table.add_column("Distance (km)", style="yellow")
            
            for activity in activities[-10:]:  # Show last 10
                distance_km = f"{activity.distance / 1000:.1f}" if activity.distance else "N/A"
                table.add_row(
                    activity.timestamp.strftime("%Y-%m-%d"),
                    activity.name[:30] + "..." if len(activity.name) > 30 else activity.name,
                    activity.activity_type,
                    distance_km
                )
            
            console.print(table)
            if len(activities) > 10:
                rprint(f"... and {len(activities) - 10} more activities")
    
    asyncio.run(_fetch())


@app.command()
def clear_data(
    source: Optional[str] = typer.Option(None, help="Filter by source"),
    data_type: Optional[str] = typer.Option(None, help="Filter by data type"),
    confirm: bool = typer.Option(False, "--yes", help="Skip confirmation")
):
    """Clear stored data."""
    async def _clear():
        storage = JsonStorage()
        
        # Show what will be deleted
        data_points = await storage.load(source=source, data_type=data_type)
        
        if not data_points:
            rprint("📊 No data to delete")
            return
        
        rprint(f"⚠️  This will delete {len(data_points)} data points")
        if source:
            rprint(f"   - Source: {source}")
        if data_type:
            rprint(f"   - Data type: {data_type}")
        
        if not confirm:
            confirm_delete = typer.confirm("Are you sure you want to delete this data?")
            if not confirm_delete:
                rprint("❌ Cancelled")
                return
        
        deleted_count = await storage.delete(source=source, data_type=data_type)
        rprint(f"✅ Deleted {deleted_count} data points")
    
    asyncio.run(_clear())


@app.command()
def export_data(
    output_file: str = typer.Option("export.json", help="Output file path"),
    source: Optional[str] = typer.Option(None, help="Filter by source"),
    data_type: Optional[str] = typer.Option(None, help="Filter by data type")
):
    """Export data to JSON file."""
    async def _export():
        storage = JsonStorage()
        data_points = await storage.load(source=source, data_type=data_type)
        
        if not data_points:
            rprint("📊 No data to export")
            return
        
        # Convert to JSON-serializable format
        export_data = [point.model_dump() for point in data_points]
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        rprint(f"✅ Exported {len(data_points)} data points to {output_file}")
    
    asyncio.run(_export())


if __name__ == "__main__":
    # Add typer as dependency if using CLI
    try:
        import typer
        from rich.console import Console
        from rich.table import Table
        from rich import print as rprint
    except ImportError:
        print("CLI dependencies not installed. Install with: uv add typer rich")
        sys.exit(1)
    
    app() 