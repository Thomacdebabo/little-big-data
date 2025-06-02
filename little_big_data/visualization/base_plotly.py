"""Base Plotly visualizer with common functionality."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from typing import List, Any, Dict

from ..core.base import DataPoint, Visualizer


class BasePlotlyVisualizer(Visualizer):
    """Base class for Plotly-based visualizers with common functionality."""
    
    def _to_dataframe(self, data_points: List[DataPoint]) -> pd.DataFrame:
        """Convert DataPoint objects to pandas DataFrame."""
        if not data_points:
            return pd.DataFrame()
        
        # Import here to avoid circular imports
        from ..models.strava import StravaActivity
        
        data = []
        for point in data_points:
            row = {
                'timestamp': point.timestamp,
                'source': point.source,
                'data_type': point.data_type,
                **point.metadata
            }
            
            # If it's a StravaActivity, extract additional fields
            if isinstance(point, StravaActivity):
                row.update({
                    'activity_id': point.activity_id,
                    'name': point.name,
                    'activity_type': point.activity_type,
                    'distance': point.distance,
                    'moving_time': point.moving_time,
                    'elapsed_time': point.elapsed_time,
                    'total_elevation_gain': point.total_elevation_gain,
                    'average_speed': point.average_speed,
                    'max_speed': point.max_speed,
                    'average_heartrate': point.average_heartrate,
                    'max_heartrate': point.max_heartrate,
                    'calories': point.calories
                })
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def to_html(self, fig: go.Figure, include_plotlyjs: str = 'cdn') -> str:
        """Convert figure to HTML string."""
        return fig.to_html(include_plotlyjs=include_plotlyjs)
    
    def _create_empty_figure(self, message: str) -> go.Figure:
        """Create an empty figure with a message."""
        return go.Figure().add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        ) 