"""Zit-specific Plotly visualizations."""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Any, Dict, Optional

from ..core.base import DataPoint
from .base_plotly import BasePlotlyVisualizer

try:
    from zit.calculate import calculate_project_times
    from zit.storage import Storage
except ImportError:
    calculate_project_times = None
    Storage = None


class ZitPlotlyVisualizer(BasePlotlyVisualizer):
    """Zit-specific Plotly visualizations."""
    
    # Stub implementations for abstract methods that don't apply to Zit
    def create_timeline(self, data_points: List[DataPoint]) -> go.Figure:
        """Not applicable for Zit data - use create_time_tracking instead."""
        return self._create_empty_figure("Use create_time_tracking for Zit data")
    
    def create_dashboard(self, data_points: List[DataPoint]) -> go.Figure:
        """Not applicable for Zit data - use create_project_summary instead."""
        return self._create_empty_figure("Use create_project_summary for Zit data")
    
    # Zit-specific visualization methods
    async def create_time_tracking(self, data_points: List[DataPoint] = None, 
                                start_date: datetime = None, end_date: datetime = None) -> go.Figure:
        """Create a time tracking visualization for zit data."""
        
        # Import ZitSource to fetch data directly
        try:
            from ..sources.zit import ZitSource
        except ImportError:
            return self._create_empty_figure("ZitSource not available")
        
        # Determine date range
        if not start_date and not end_date:
            if data_points:
                # Extract date range from data points
                zit_data = [dp for dp in data_points if dp.source == "zit"]
                if zit_data:
                    timestamps = [dp.timestamp for dp in zit_data]
                    start_date = min(timestamps)
                    end_date = max(timestamps)
                else:
                    # Default to last 7 days
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=7)
            else:
                # Default to last 7 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
        
        # Fetch data directly from ZitSource
        zit_source = ZitSource()
        
        try:
            # Use the multi-day summary for accurate time calculations
            summary_data = await zit_source.get_multi_day_summary(start_date, end_date)
            
            if not summary_data['total_project_times']:
                return self._create_empty_figure("No project time data found")
            
            # Get detailed sessions for visualization
            all_sessions = []
            
            # Get available dates in range
            available_dates = zit_source.get_available_dates()
            
            for date_str in available_dates:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    if start_date.date() <= date_obj.date() <= end_date.date():
                        # Get raw events for this date to create sessions
                        if Storage:
                            zit_storage = Storage(date_str)
                            events = zit_storage.get_events()
                            
                            exclude_projects = ['STOP', 'LUNCH']
                            
                            # Create sessions from events
                            for i in range(len(events) - 1):
                                current = events[i]
                                next_event = events[i + 1]
                                
                                # Skip if current project is excluded
                                if current.name in exclude_projects:
                                    continue
                                
                                duration = (next_event.timestamp - current.timestamp).total_seconds() / 3600
                                
                                all_sessions.append({
                                    'project': current.name,
                                    'start': current.timestamp,
                                    'end': next_event.timestamp,
                                    'duration': duration
                                })
                except ValueError:
                    continue
            
            if not all_sessions:
                return self._create_empty_figure("No project sessions found")
            
            # Create Gantt-like chart
            fig = go.Figure()
            
            # Convert total times from seconds to hours
            project_times = {k: v/3600 for k, v in summary_data['total_project_times'].items()}
            
            projects = list(project_times.keys())
            colors = px.colors.qualitative.Set3
            project_colors = {project: colors[i % len(colors)] for i, project in enumerate(projects)}
            
            for session in all_sessions:
                project = session['project']
                if project in project_colors:  # Only show sessions for non-excluded projects
                    fig.add_trace(go.Scatter(
                        x=[session['start'], session['end']],
                        y=[project, project],
                        mode='lines',
                        line=dict(width=20, color=project_colors[project]),
                        name=f"{project} ({project_times[project]:.1f}h)",
                        showlegend=True,
                        hovertemplate=f'<b>{project}</b><br>' +
                                    'Start: %{x[0]}<br>' +
                                    'End: %{x[1]}<br>' +
                                    f'Duration: {session["duration"]:.1f}h<br>' +
                                    '<extra></extra>'
                    ))
            
            fig.update_layout(
                title="Time Tracking - Project Sessions",
                xaxis_title="Time",
                yaxis_title="Projects",
                height=max(400, len(projects) * 50),
                hovermode='closest'
            )
            
            return fig
            
        except Exception as e:
            return self._create_empty_figure(f"Error fetching zit data: {str(e)}")
    
    async def create_daily_breakdown(self, data_points: List[DataPoint], target_date: Any) -> go.Figure:
        """Create a daily breakdown visualization for zit data."""
        
        # Import ZitSource to fetch data directly
        try:
            from ..sources.zit import ZitSource
        except ImportError:
            return self._create_empty_figure("ZitSource not available")
        
        # Convert target_date to date object if it's a string
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        elif hasattr(target_date, 'date'):
            target_date = target_date.date()
        
        # Fetch data directly from ZitSource
        zit_source = ZitSource()
        target_datetime = datetime.combine(target_date, datetime.min.time())
        
        try:
            # Get daily summary with correct time calculations
            daily_summary = await zit_source.get_daily_summary(target_datetime)
            
            if not daily_summary['project_times']:
                return self._create_empty_figure(f"No productive time found for {target_date}")
            
            # Convert project times from seconds to hours
            project_times = {k: v/3600 for k, v in daily_summary['project_times'].items()}
            
            # Get timeline data from raw events
            timeline_data = []
            date_str = target_date.strftime('%Y-%m-%d')
            
            if Storage:
                zit_storage = Storage(date_str)
                events = zit_storage.get_events()
                
                exclude_projects = ['STOP', 'LUNCH']
                
                for i in range(len(events) - 1):
                    current = events[i]
                    next_event = events[i + 1]
                    
                    # Skip if current project is excluded
                    if current.name in exclude_projects:
                        continue
                        
                    duration = (next_event.timestamp - current.timestamp).total_seconds() / 3600
                    
                    timeline_data.append({
                        'project': current.name,
                        'start': current.timestamp,
                        'end': next_event.timestamp,
                        'duration': duration
                    })
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(
                    f"Daily Timeline - {target_date}",
                    "Time Distribution by Project"
                ),
                row_heights=[0.6, 0.4],
                specs=[[{"secondary_y": False}], [{"type": "domain"}]]
            )
            
            # Timeline view
            colors = px.colors.qualitative.Set3
            project_colors = {project: colors[i % len(colors)] for i, project in enumerate(project_times.keys())}
            
            for entry in timeline_data:
                fig.add_trace(
                    go.Scatter(
                        x=[entry['start'], entry['end']],
                        y=[entry['project'], entry['project']],
                        mode='lines',
                        line=dict(width=15, color=project_colors.get(entry['project'], 'gray')),
                        name=entry['project'],
                        showlegend=False,
                        hovertemplate=f'<b>{entry["project"]}</b><br>' +
                                    'Start: %{x[0]|%H:%M}<br>' +
                                    'End: %{x[1]|%H:%M}<br>' +
                                    f'Duration: {entry["duration"]:.1f}h<br>' +
                                    '<extra></extra>'
                    ),
                    row=1, col=1
                )
            
            # Pie chart
            if project_times:
                fig.add_trace(
                    go.Pie(
                        labels=list(project_times.keys()),
                        values=list(project_times.values()),  # Already in hours
                        textinfo='label+percent',
                        textposition='auto',
                        marker=dict(colors=[project_colors.get(p, 'gray') for p in project_times.keys()]),
                        hovertemplate='<b>%{label}</b><br>' +
                                    'Time: %{value:.1f}h<br>' +
                                    'Percentage: %{percent}<br>' +
                                    '<extra></extra>'
                    ),
                    row=2, col=1
                )
            
            fig.update_layout(
                title=f"Daily Time Tracking - {target_date}",
                height=800,
                showlegend=True
            )
            
            # Update timeline axes
            fig.update_xaxes(title_text="Time of Day", row=1, col=1)
            fig.update_yaxes(title_text="Projects", row=1, col=1)
            
            return fig
            
        except Exception as e:
            return self._create_empty_figure(f"Error fetching zit data for {target_date}: {str(e)}")
    
    async def create_project_summary(self, data_points: List[DataPoint] = None,
                                  ) -> go.Figure:
        """Create a project summary visualization for zit data."""
        
        # Import ZitSource to fetch data directly
        try:
            from ..sources.zit import ZitSource
        except ImportError:
            return self._create_empty_figure("ZitSource not available")
        
        # Fetch data directly from ZitSource
        zit_source = ZitSource()
        
        try:
            # Get multi-day summary
            dates = zit_source.get_available_dates()
            start_date = datetime.strptime(min(dates), '%Y-%m-%d')
            end_date = datetime.strptime(max(dates), '%Y-%m-%d')
            summary_data = await zit_source.get_multi_day_summary(start_date, end_date)
            
            if not summary_data['daily_summaries']:
                return self._create_empty_figure("No project data found")
            
            # Extract daily project times and convert to hours
            daily_project_times = {}
            total_project_times = {}  # Track total time per project
            
            for date_str, daily_summary in summary_data['daily_summaries'].items():
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                daily_project_times[date_obj] = {
                    k: v/3600 for k, v in daily_summary['project_times'].items()
                }
                # Accumulate total times
                for project, hours in daily_project_times[date_obj].items():
                    if project not in total_project_times:
                        total_project_times[project] = 0
                    total_project_times[project] += hours
            
            # Create subplots: stacked bar chart and project totals
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Project Time Summary", "Total Time by Project"),
                vertical_spacing=0.2,
                row_heights=[0.7, 0.3]
            )
            
            all_projects = set()
            for day_data in daily_project_times.values():
                all_projects.update(day_data.keys())
            
            all_projects = sorted(list(all_projects))
            colors = px.colors.qualitative.Set3
            
            # Add stacked bar chart
            for i, project in enumerate(all_projects):
                x_values = []
                y_values = []
                
                for date, project_data in sorted(daily_project_times.items()):
                    x_values.append(date)
                    y_values.append(project_data.get(project, 0))
                
                fig.add_trace(go.Bar(
                    x=x_values,
                    y=y_values,
                    name=project,
                    marker_color=colors[i % len(colors)],
                    hovertemplate=f'<b>{project}</b><br>' +
                                'Date: %{x}<br>' +
                                'Hours: %{y:.1f}<br>' +
                                '<extra></extra>'
                ), row=1, col=1)
            
            # Add project totals bar chart
            sorted_projects = sorted(total_project_times.items(), key=lambda x: x[1], reverse=True)
            fig.add_trace(go.Bar(
                x=[p[0] for p in sorted_projects],
                y=[p[1] for p in sorted_projects],
                marker_color=colors,
                hovertemplate='<b>%{x}</b><br>' +
                            'Total Hours: %{y:.1f}<br>' +
                            '<extra></extra>'
            ), row=2, col=1)
            
            fig.update_layout(
                height=900,
                barmode='stack',
                hovermode='x unified',
                showlegend=True
            )
            
            # Update axes
            fig.update_xaxes(title_text="Date", row=1, col=1)
            fig.update_yaxes(title_text="Hours", row=1, col=1)
            fig.update_xaxes(title_text="Project", row=2, col=1)
            fig.update_yaxes(title_text="Total Hours", row=2, col=1)
            
            return fig
            
        except Exception as e:
            return self._create_empty_figure(f"Error fetching zit data: {str(e)}")