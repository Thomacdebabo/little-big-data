"""Plotly-based visualization implementation."""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
from typing import List, Any, Dict, Optional

from ..core.base import DataPoint, Visualizer
from ..models.strava import StravaActivity


class PlotlyVisualizer(Visualizer):
    """Plotly-based visualizer for creating interactive charts."""
    
    def create_timeline(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a timeline visualization of activities."""
        if not data_points:
            return go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Convert to DataFrame for easier manipulation
        df = self._to_dataframe(data_points)
        
        # Create timeline plot
        fig = go.Figure()
        
        # Group by activity type for different colors
        activity_types = df['activity_type'].unique() if 'activity_type' in df.columns else ['activity']
        colors = px.colors.qualitative.Set3
        
        for i, activity_type in enumerate(activity_types):
            type_data = df[df['activity_type'] == activity_type] if 'activity_type' in df.columns else df
            
            # Create scatter plot for this activity type
            fig.add_trace(go.Scatter(
                x=type_data['timestamp'],
                y=[activity_type] * len(type_data),
                mode='markers',
                marker=dict(
                    size=10,
                    color=colors[i % len(colors)],
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                name=activity_type,
                text=type_data.get('name', type_data['timestamp'].dt.strftime('%Y-%m-%d')),
                hovertemplate='<b>%{text}</b><br>' +
                            'Date: %{x}<br>' +
                            'Type: %{y}<br>' +
                            '<extra></extra>'
            ))
        
        fig.update_layout(
            title="Activity Timeline",
            xaxis_title="Date",
            yaxis_title="Activity Type",
            hovermode='closest',
            showlegend=True,
            height=500
        )
        
        return fig
    
    def create_dashboard(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a comprehensive dashboard with multiple views."""
        if not data_points:
            return go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = self._to_dataframe(data_points)
        
        # Create subplots with proper specs for pie chart
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Activities Over Time",
                "Distance Distribution",
                "Activity Types",
                "Weekly Activity Count"
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"type": "domain"}, {"secondary_y": False}]  # domain type for pie chart
            ]
        )
        
        # 1. Activities over time (timeline)
        if 'activity_type' in df.columns and len(df) > 0:
            activity_types = df['activity_type'].unique()
            colors = px.colors.qualitative.Set3
            
            for i, activity_type in enumerate(activity_types):
                type_data = df[df['activity_type'] == activity_type]
                fig.add_trace(
                    go.Scatter(
                        x=type_data['timestamp'],
                        y=type_data.get('distance', [1] * len(type_data)),
                        mode='markers',
                        marker=dict(color=colors[i % len(colors)]),
                        name=activity_type,
                        showlegend=True
                    ),
                    row=1, col=1
                )
        
        # 2. Distance distribution
        if 'distance' in df.columns and len(df) > 0:
            distances = df['distance'].dropna()
            if len(distances) > 0:
                fig.add_trace(
                    go.Histogram(
                        x=distances / 1000,  # Convert to km
                        nbinsx=20,
                        name="Distance",
                        showlegend=False,
                        marker_color='lightblue'
                    ),
                    row=1, col=2
                )
        
        # 3. Activity types pie chart
        if 'activity_type' in df.columns and len(df) > 0:
            activity_counts = df['activity_type'].value_counts()
            if len(activity_counts) > 0:
                fig.add_trace(
                    go.Pie(
                        labels=activity_counts.index,
                        values=activity_counts.values,
                        name="Activity Types",
                        showlegend=False
                    ),
                    row=2, col=1
                )
        
        # 4. Weekly activity count
        if len(df) > 0:
            df['week'] = df['timestamp'].dt.to_period('W').astype(str)
            weekly_counts = df.groupby('week').size()
            if len(weekly_counts) > 0:
                fig.add_trace(
                    go.Bar(
                        x=weekly_counts.index,
                        y=weekly_counts.values,
                        name="Weekly Count",
                        showlegend=False,
                        marker_color='green'
                    ),
                    row=2, col=2
                )
        
        # Update layout
        fig.update_layout(
            title_text="Activity Dashboard",
            height=800,
            showlegend=True
        )
        
        # Update axis labels
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Distance (m)", row=1, col=1)
        fig.update_xaxes(title_text="Distance (km)", row=1, col=2)
        fig.update_yaxes(title_text="Count", row=1, col=2)
        fig.update_xaxes(title_text="Week", row=2, col=2)
        fig.update_yaxes(title_text="Activity Count", row=2, col=2)
        
        return fig
    
    def create_activity_heatmap(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a heatmap showing activity patterns by day of week and hour."""
        if not data_points:
            return go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = self._to_dataframe(data_points)
        
        # Extract day of week and hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['hour'] = df['timestamp'].dt.hour
        
        # Create pivot table for heatmap
        heatmap_data = df.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(day_order)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='Viridis',
            hovertemplate='Day: %{y}<br>Hour: %{x}<br>Activities: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Activity Heatmap by Day and Hour",
            xaxis_title="Hour of Day",
            yaxis_title="Day of Week",
            height=400
        )
        
        return fig
    
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