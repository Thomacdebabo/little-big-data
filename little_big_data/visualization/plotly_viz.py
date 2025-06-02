"""Plotly-based visualization implementation."""

import plotly.graph_objects as go
from datetime import datetime
from typing import List, Any, Dict, Optional

from ..core.base import DataPoint, Visualizer
from .base_plotly import BasePlotlyVisualizer
from .strava_plotly import StravaPlotlyVisualizer
from .zit_plotly import ZitPlotlyVisualizer


class PlotlyVisualizer(BasePlotlyVisualizer):
    """Main Plotly-based visualizer that coordinates specialized visualizers."""
    
    def __init__(self):
        super().__init__()
        self.strava_viz = StravaPlotlyVisualizer()
        self.zit_viz = ZitPlotlyVisualizer()
    
    # Strava visualizations
    def create_timeline(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a timeline visualization of activities."""
        return self.strava_viz.create_timeline(data_points)
    
    def create_dashboard(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a comprehensive dashboard with multiple views."""
        return self.strava_viz.create_dashboard(data_points)
    
    def create_activity_heatmap(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a heatmap showing running patterns by week and hour of day."""
        return self.strava_viz.create_activity_heatmap(data_points)
    
    def create_weekly_running_stats(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a visualization showing weekly average pace and run length."""
        return self.strava_viz.create_weekly_running_stats(data_points)
    
    # Zit visualizations
    async def create_zit_time_tracking(self, data_points: List[DataPoint] = None, 
                                start_date: datetime = None, end_date: datetime = None) -> go.Figure:
        """Create a time tracking visualization for zit data."""
        return await self.zit_viz.create_time_tracking(data_points, start_date, end_date)
    
    async def create_zit_daily_breakdown(self, data_points: List[DataPoint], target_date: Any) -> go.Figure:
        """Create a daily breakdown visualization for zit data."""
        return await self.zit_viz.create_daily_breakdown(data_points, target_date)
    
    async def create_zit_project_summary(self, data_points: List[DataPoint] = None,
                                  start_date: datetime = None, end_date: datetime = None) -> go.Figure:
        """Create a project summary visualization for zit data."""
        return await self.zit_viz.create_project_summary(data_points) 