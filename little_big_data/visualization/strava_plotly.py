"""Strava-specific Plotly visualizations."""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
from typing import List, Any, Dict, Optional

from ..core.base import DataPoint
from .base_plotly import BasePlotlyVisualizer


class StravaPlotlyVisualizer(BasePlotlyVisualizer):
    """Strava-specific Plotly visualizations."""
    
    def create_timeline(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a timeline visualization of activities."""
        if not data_points:
            return self._create_empty_figure("No data available")
        
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
            return self._create_empty_figure("No data available")
        
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
        """Create a heatmap showing running patterns by week and hour of day."""
        if not data_points:
            return self._create_empty_figure("No data available")
        
        df = self._to_dataframe(data_points)
        
        # Filter for running activities only
        if 'activity_type' in df.columns:
            run_activities = df[df['activity_type'].str.lower().isin(['run', 'running'])]
        else:
            # If no activity type, assume all are runs
            run_activities = df
        
        if len(run_activities) == 0:
            return self._create_empty_figure("No running activities found")
        
        # Extract month and hour
        run_activities = run_activities.copy()
        run_activities['month'] = run_activities['timestamp'].dt.to_period('M')
        run_activities['hour'] = run_activities['timestamp'].dt.hour
        
        # Create pivot table for heatmap (hour vs month)
        heatmap_data = run_activities.groupby(['hour', 'month']).size().unstack(fill_value=0)
        
        # Convert month periods to strings for better display
        heatmap_data.columns = heatmap_data.columns.astype(str)
        
        # Ensure all hours 0-23 are represented
        all_hours = list(range(24))
        for hour in all_hours:
            if hour not in heatmap_data.index:
                heatmap_data.loc[hour] = 0
        
        # Sort index (hours) in order
        heatmap_data = heatmap_data.sort_index()
        
        # Create more readable month labels and determine tick spacing
        month_labels = []
        month_positions = []
        total_months = len(heatmap_data.columns)
        
        # Show approximately every 3-4 months for readability
        tick_interval = max(1, 3)  # Show every 3 months
        
        for i, month_str in enumerate(heatmap_data.columns):
            if i % tick_interval == 0:
                # Parse the month string to get a readable format
                try:
                    # Month format is like "2019-10"
                    year, month = month_str.split('-')
                    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    month_name = month_names[int(month)]
                    readable_label = f"{month_name} {year}"
                    month_labels.append(readable_label)
                    month_positions.append(i)
                except:
                    # Fallback to original string if parsing fails
                    month_labels.append(month_str)
                    month_positions.append(i)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=list(range(len(heatmap_data.columns))),  # Use numeric positions
            y=heatmap_data.index,
            colorscale='Viridis',
            hovertemplate='Month: %{customdata}<br>Hour: %{y}:00<br>Runs: %{z}<extra></extra>',
            customdata=[heatmap_data.columns] * len(heatmap_data.index),  # Show original month strings in hover
            colorbar=dict(title="Number of Runs")
        ))
        
        fig.update_layout(
            title="Running Heatmap: Frequency by Month and Hour of Day",
            xaxis_title="Time Period",
            yaxis_title="Hour of Day",
            height=600,
            yaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=2  # Show every 2 hours
            ),
            xaxis=dict(
                tickmode='array',
                tickvals=month_positions,
                ticktext=month_labels,
                tickangle=45  # Angle labels for better readability
            )
        )
        
        return fig
    
    def create_weekly_running_stats(self, data_points: List[DataPoint]) -> go.Figure:
        """Create a visualization showing weekly average pace and run length."""
        if not data_points:
            return self._create_empty_figure("No data available")
        
        df = self._to_dataframe(data_points)
        
        # Filter for running activities only
        if 'activity_type' in df.columns:
            run_activities = df[df['activity_type'].str.lower().isin(['run', 'running'])]
        else:
            # If no activity type, assume all are runs
            run_activities = df
        
        if len(run_activities) == 0:
            return self._create_empty_figure("No running activities found")
        
        # Filter out activities with missing required data
        run_activities = run_activities.dropna(subset=['distance', 'moving_time'])
        run_activities = run_activities[
            (run_activities['distance'] > 0) & 
            (run_activities['moving_time'] > 0)
        ]
        
        if len(run_activities) == 0:
            return self._create_empty_figure("No valid running data found (missing distance or time)")
        
        # Calculate pace (minutes per km)
        run_activities = run_activities.copy()
        run_activities['distance_km'] = run_activities['distance'] / 1000.0
        run_activities['pace_min_per_km'] = (run_activities['moving_time'] / 60.0) / run_activities['distance_km']
        
        # Group by week
        run_activities['week'] = run_activities['timestamp'].dt.to_period('W')
        
        # Calculate weekly statistics
        weekly_stats = run_activities.groupby('week').agg({
            'pace_min_per_km': 'mean',
            'distance_km': 'sum',
            'distance': 'count'  # Number of runs per week
        }).reset_index()
        
        # Convert week period to string for plotting
        weekly_stats['week_str'] = weekly_stats['week'].astype(str)
        weekly_stats['week_start'] = weekly_stats['week'].apply(lambda x: x.start_time)
        
        # Debug: Check if we have data
        if len(weekly_stats) == 0:
            return self._create_empty_figure("No weekly statistics calculated")
        
        # Create subplot with secondary y-axis and timeline
        fig = make_subplots(
            rows=2, cols=1,
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
            row_heights=[0.7, 0.3],
            vertical_spacing=0.05,  # Reduced spacing between subplots
            subplot_titles=["Weekly Running Statistics", "Timeline"]
        )
        
        # Add average pace line
        fig.add_trace(
            go.Scatter(
                x=weekly_stats['week_start'],
                y=weekly_stats['pace_min_per_km'],
                mode='lines+markers',
                name='Average Pace (min/km)',
                line=dict(color='blue', width=2),
                marker=dict(size=6),
                hovertemplate='Week: %{x}<br>Pace: %{y:.2f} min/km<extra></extra>'
            ),
            row=1, col=1,
            secondary_y=False
        )
        
        # Add average distance line
        fig.add_trace(
            go.Bar(
                x=weekly_stats['week_start'],
                y=weekly_stats['distance_km'],
                name='Sum Distance (km)',
                marker=dict(color='red', opacity=0.7),
                hovertemplate='Week: %{x}<br>Distance: %{y:.2f} km<extra></extra>'
            ),
            row=1, col=1,
            secondary_y=True
        )
        
        # Add number of runs as bar chart (subtle background)
        fig.add_trace(
            go.Bar(
                x=weekly_stats['week_start'],
                y=weekly_stats['distance'] * 0.1,  # Scale down to not interfere with main data
                name='Runs per Week (scaled)',
                opacity=0.2,
                marker_color='lightgray',
                hovertemplate='Week: %{x}<br>Number of runs: %{customdata}<extra></extra>',
                customdata=weekly_stats['distance']  # Show actual count in hover
            ),
            row=1, col=1,
            secondary_y=False
        )
        
        # Add timeline markers with notes - organized into separate categories
        # Support both single events and ranges
        timeline_categories = [
                {
                'name': 'Spring',
                'entries': [
                    {'type': 'range', 'start_timestamp': '2020-04-01', 'end_timestamp': '2020-08-01', 'note': '2020'},
                    {'type': 'range', 'start_timestamp': '2021-04-01', 'end_timestamp': '2021-08-01', 'note': '2021'},
                    {'type': 'range', 'start_timestamp': '2022-04-01', 'end_timestamp': '2022-08-01', 'note': '2022'},
                    {'type': 'range', 'start_timestamp': '2023-04-01', 'end_timestamp': '2023-08-01', 'note': '2023'},
                    {'type': 'range', 'start_timestamp': '2024-04-01', 'end_timestamp': '2024-08-01', 'note': '2024'},
                    {'type': 'range', 'start_timestamp': '2025-04-01', 'end_timestamp': '2025-08-01', 'note': '2025'},
                ]
            },
            {
                'name': 'Ski Teaching',
                'entries': [
                    {'type': 'range', 'start_timestamp': '2022-12-24', 'end_timestamp': '2023-03-01', 'note': 'SSSE'},
                    {'type': 'range', 'start_timestamp': '2023-12-25', 'end_timestamp': '2024-03-01', 'note': 'SSSF'},
                    {'type': 'single', 'timestamp': '2025-02-01', 'note': 'SCS start'},
                ]
            },
            {
                'name': 'Health Events',
                'entries': [
                    {'type': 'single', 'timestamp': '2024-08-19', 'note': 'Keuchhusten'},
                ]
            },
            {
                'name': 'Others',
                'entries': [
                    {'type': 'single', 'timestamp': '2020-05-13', 'note': 'Birthday'},
                    {'type': 'single', 'timestamp': '2021-05-13', 'note': 'Birthday'},
                    {'type': 'single', 'timestamp': '2022-05-13', 'note': 'Birthday'},
                    {'type': 'single', 'timestamp': '2023-05-13', 'note': 'Birthday'},
                    {'type': 'single', 'timestamp': '2024-05-13', 'note': 'Birthday'},
                    {'type': 'single', 'timestamp': '2025-05-13', 'note': 'Birthday'},
                ]
            }
        ]
        
        # Convert timestamps to datetime and add vertical lines for all events
        all_timeline_dates = []
        all_timeline_notes = []
        
        for category in timeline_categories:
            for entry in category['entries']:
                if entry['type'] == 'single':
                    date = datetime.strptime(entry['timestamp'], '%Y-%m-%d')
                    all_timeline_dates.append(date)
                    all_timeline_notes.append(entry['note'])
                    
                    # Add vertical line to main plot
                    fig.add_vline(
                        x=date,
                        line_dash="dash",
                        line_color="gray",
                        opacity=0.5,
                        row=1, col=1
                    )
                elif entry['type'] == 'range':
                    start_date = datetime.strptime(entry['start_timestamp'], '%Y-%m-%d')
                    end_date = datetime.strptime(entry['end_timestamp'], '%Y-%m-%d')
                    all_timeline_dates.extend([start_date, end_date])
                    all_timeline_notes.extend([f"{entry['note']} start", f"{entry['note']} end"])
                    
                    # Add vertical lines for range start and end
                    fig.add_vline(
                        x=start_date,
                        line_dash="dash",
                        line_color="gray",
                        opacity=0.5,
                        row=1, col=1
                    )
                    fig.add_vline(
                        x=end_date,
                        line_dash="dash",
                        line_color="gray",
                        opacity=0.5,
                        row=1, col=1
                    )
        
        # Add timeline markers for each category on separate y-levels
        colors = ['blue', 'green', 'orange', 'purple', 'brown']  # Different colors for categories
        
        for i, category in enumerate(timeline_categories):
            # Handle single events
            single_events = [entry for entry in category['entries'] if entry['type'] == 'single']
            if single_events:
                single_dates = [datetime.strptime(entry['timestamp'], '%Y-%m-%d') for entry in single_events]
                single_notes = [entry['note'] for entry in single_events]
                
                fig.add_trace(
                    go.Scatter(
                        x=single_dates,
                        y=[i] * len(single_dates),  # Different y-level for each category
                        mode='markers+text',
                        name=f"{category['name']} (Events)",
                        marker=dict(
                            size=8,
                            color=colors[i % len(colors)],
                            symbol='circle'
                        ),
                        text=single_notes,
                        textposition='top center',
                        hovertemplate='Date: %{x}<br>Note: %{text}<br>Category: ' + category['name'] + '<extra></extra>'
                    ),
                    row=2, col=1
                )
            
            # Handle range events
            range_events = [entry for entry in category['entries'] if entry['type'] == 'range']
            for j, range_entry in enumerate(range_events):
                start_date = datetime.strptime(range_entry['start_timestamp'], '%Y-%m-%d')
                end_date = datetime.strptime(range_entry['end_timestamp'], '%Y-%m-%d')
                
                # Add connecting bar for range
                fig.add_trace(
                    go.Scatter(
                        x=[start_date, end_date],
                        y=[i, i],
                        mode='lines+markers',
                        name=f"{category['name']} ({range_entry['note']})",
                        opacity=0.8,
                        line=dict(
                            color=colors[i % len(colors)],
                            width=6
                        ),
                        marker=dict(
                            size=10,
                            color=colors[i % len(colors)],
                            symbol=['circle', 'circle'],
                        ),
                        showlegend=False,
                        hovertemplate='Date: %{x}<br>Note: ' + range_entry['note'] + '<br>Category: ' + category['name'] + '<extra></extra>'
                    ),
                    row=2, col=1
                )
                
                # Add text label in the middle of the range
                middle_date = start_date + (end_date - start_date) / 2
                fig.add_trace(
                    go.Scatter(
                        x=[middle_date],
                        y=[i],
                        mode='text',
                        text=[range_entry['note']],
                        textposition='middle center',
                        textfont=dict(color='white', size=10),
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=2, col=1
                )
        
        # Update layout
        fig.update_layout(
            title={
                'text': "Weekly Running Statistics",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Week",
            hovermode='x unified',
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Update y-axes for main plot
        fig.update_yaxes(
            title_text="Average Pace (minutes per km)",
            secondary_y=False,
            showgrid=True,
            gridcolor='lightblue',
            gridwidth=1,
            row=1, col=1
        )
        fig.update_yaxes(
            title_text="Average Distance (km)",
            secondary_y=True,
            showgrid=False,
            row=1, col=1
        )
        
        # Configure x-axes to align between subplots
        fig.update_xaxes(
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            range=[weekly_stats['week_start'].min(), weekly_stats['week_start'].max()],  # Align x-axis ranges
            row=1, col=1
        )
        
        # Configure timeline subplot
        fig.update_xaxes(
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            tickangle=45,
            range=[weekly_stats['week_start'].min(), weekly_stats['week_start'].max()],  # Align x-axis ranges
            row=2, col=1
        )
        fig.update_yaxes(
            showticklabels=True,
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            tickmode='array',
            tickvals=list(range(len(timeline_categories))),
            ticktext=[category['name'] for category in timeline_categories],
            range=[-0.5, len(timeline_categories) - 0.5],
            row=2, col=1
        )
        
        return fig 