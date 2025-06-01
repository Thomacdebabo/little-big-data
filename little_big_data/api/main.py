"""FastAPI web application."""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os
from pathlib import Path
from pydantic import BaseModel

from ..core.base import DataPoint
from ..storage.json_storage import JsonStorage
from ..sources.strava import StravaSource
from ..visualization.plotly_viz import PlotlyVisualizer
from ..models.strava import StravaActivity

app = FastAPI(
    title="Little Big Data",
    description="Personal data aggregation and visualization framework",
    version="0.1.0"
)

# Initialize storage and visualizer
storage = JsonStorage()
visualizer = PlotlyVisualizer()

# Templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Request models
class StravaFetchRequest(BaseModel):
    access_token: str
    days_back: Optional[int] = 30
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with navigation."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/data/sources")
async def list_sources():
    """List available data sources."""
    return {
        "sources": [
            {
                "name": "strava",
                "description": "Strava fitness activities",
                "data_types": ["activity"],
                "status": "available"
            }
        ]
    }


@app.get("/data/summary")
async def data_summary():
    """Get summary of stored data."""
    try:
        all_data = await storage.load()
        
        summary = {
            "total_points": len(all_data),
            "sources": {},
            "date_range": None
        }
        
        if all_data:
            # Group by source
            for point in all_data:
                source = point.source
                if source not in summary["sources"]:
                    summary["sources"][source] = {
                        "count": 0,
                        "data_types": set(),
                        "date_range": {"start": None, "end": None}
                    }
                
                summary["sources"][source]["count"] += 1
                summary["sources"][source]["data_types"].add(point.data_type)
                
                # Update date range
                if summary["sources"][source]["date_range"]["start"] is None or \
                   point.timestamp < summary["sources"][source]["date_range"]["start"]:
                    summary["sources"][source]["date_range"]["start"] = point.timestamp
                
                if summary["sources"][source]["date_range"]["end"] is None or \
                   point.timestamp > summary["sources"][source]["date_range"]["end"]:
                    summary["sources"][source]["date_range"]["end"] = point.timestamp
            
            # Convert sets to lists and dates to strings
            for source_info in summary["sources"].values():
                source_info["data_types"] = list(source_info["data_types"])
                if source_info["date_range"]["start"]:
                    source_info["date_range"]["start"] = source_info["date_range"]["start"].isoformat()
                if source_info["date_range"]["end"]:
                    source_info["date_range"]["end"] = source_info["date_range"]["end"].isoformat()
            
            # Overall date range
            timestamps = [point.timestamp for point in all_data]
            summary["date_range"] = {
                "start": min(timestamps).isoformat(),
                "end": max(timestamps).isoformat()
            }
        
        return summary
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data")
async def get_data(
    source: Optional[str] = Query(None, description="Filter by data source"),
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: Optional[int] = Query(100, description="Maximum number of items to return")
):
    """Get data points with optional filtering."""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Load data
        data_points = await storage.load(
            source=source,
            data_type=data_type,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Apply limit
        if limit and len(data_points) > limit:
            data_points = data_points[:limit]
        
        # Convert to JSON-serializable format
        return {
            "count": len(data_points),
            "data": [point.model_dump() for point in data_points]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/data/strava/fetch")
async def fetch_strava_data(request: StravaFetchRequest):
    """Fetch data from Strava API."""
    try:
        # Initialize Strava source
        config = {
            "access_token": request.access_token,
            "client_id": request.client_id,
            "client_secret": request.client_secret,
            "refresh_token": request.refresh_token
        }
        
        strava = StravaSource(config)
        
        # Authenticate
        if not await strava.authenticate():
            raise HTTPException(status_code=401, detail="Failed to authenticate with Strava")
        
        # Set date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days_back) if request.days_back else None
        
        # Fetch data
        activities = await strava.fetch_data(start_date=start_date, end_date=end_date)
        
        # Save to storage
        await storage.save(activities)
        
        return {
            "success": True,
            "message": f"Fetched and saved {len(activities)} activities",
            "count": len(activities)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualizations/timeline", response_class=HTMLResponse)
async def timeline_visualization(
    source: Optional[str] = Query(None),
    data_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Generate timeline visualization."""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Load data
        data_points = await storage.load(
            source=source,
            data_type=data_type,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Create visualization
        fig = visualizer.create_timeline(data_points)
        
        return HTMLResponse(visualizer.to_html(fig))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualizations/dashboard", response_class=HTMLResponse)
async def dashboard_visualization(
    source: Optional[str] = Query(None),
    data_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Generate dashboard visualization."""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Load data
        data_points = await storage.load(
            source=source,
            data_type=data_type,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Create visualization
        fig = visualizer.create_dashboard(data_points)
        
        return HTMLResponse(visualizer.to_html(fig))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualizations/heatmap", response_class=HTMLResponse)
async def heatmap_visualization(
    source: Optional[str] = Query(None),
    data_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Generate activity heatmap visualization."""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Load data
        data_points = await storage.load(
            source=source,
            data_type=data_type,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Create visualization
        fig = visualizer.create_activity_heatmap(data_points)
        
        return HTMLResponse(visualizer.to_html(fig))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualizations/weekly-running-stats", response_class=HTMLResponse)
async def weekly_running_stats_visualization(
    source: Optional[str] = Query(None),
    data_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Generate weekly running statistics visualization showing average pace and distance."""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Load data
        data_points = await storage.load(
            source=source,
            data_type=data_type,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Create visualization
        fig = visualizer.create_weekly_running_stats(data_points)
        
        return HTMLResponse(visualizer.to_html(fig))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/data")
async def delete_data(
    source: Optional[str] = Query(None),
    data_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Delete data points."""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Delete data
        deleted_count = await storage.delete(
            source=source,
            data_type=data_type,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} data points",
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Strava OAuth endpoints
@app.get("/auth/strava/url")
async def get_strava_auth_url(
    client_id: str,
    redirect_uri: str = "http://localhost:8000/auth/strava/callback"
):
    """Get Strava OAuth authorization URL."""
    try:
        auth_url = StravaSource.get_authorization_url(client_id, redirect_uri)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/strava/callback")
async def strava_oauth_callback(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """Handle Strava OAuth callback."""
    if error:
        # OAuth error occurred
        return HTMLResponse(f"""
        <html>
            <head><title>Strava Authorization Error</title></head>
            <body>
                <h1>Authorization Error</h1>
                <p>Error: {error}</p>
                <p>Description: {error_description or 'No description provided'}</p>
                <p><a href="/">Return to Home</a></p>
            </body>
        </html>
        """, status_code=400)
    
    if not code:
        # No authorization code received
        return HTMLResponse("""
        <html>
            <head><title>Strava Authorization</title></head>
            <body>
                <h1>Authorization Required</h1>
                <p>No authorization code received from Strava.</p>
                <p><a href="/">Return to Home</a></p>
            </body>
        </html>
        """, status_code=400)
    
    # Authorization successful - display the code for manual exchange
    return HTMLResponse(f"""
    <html>
        <head><title>Strava Authorization Successful</title></head>
        <body>
            <h1>Strava Authorization Successful!</h1>
            <p>Authorization code received: <code>{code}</code></p>
            <p>You can now use this code with the <code>/auth/strava/token</code> endpoint to exchange it for access tokens.</p>
            <p>Or use the API documentation at <a href="/docs">/docs</a> to complete the token exchange.</p>
            <p><a href="/">Return to Home</a></p>
        </body>
    </html>
    """)


@app.post("/auth/strava/token")
async def exchange_strava_token(
    client_id: str,
    client_secret: str,
    code: str
):
    """Exchange Strava authorization code for access token."""
    try:
        token_data = await StravaSource.exchange_code_for_token(
            client_id, client_secret, code
        )
        return token_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 