"""Unit tests for visualization components."""

import pytest
import plotly.graph_objects as go
from datetime import datetime, timezone

from little_big_data.visualization.plotly_viz import PlotlyVisualizer
from little_big_data.core.base import DataPoint


class TestPlotlyVisualizer:
    """Test the PlotlyVisualizer implementation."""
    
    def test_init(self):
        """Test visualizer initialization."""
        visualizer = PlotlyVisualizer()
        assert isinstance(visualizer, PlotlyVisualizer)
    
    def test_create_timeline_empty_data(self):
        """Test creating timeline with empty data."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_timeline([])
        
        assert isinstance(fig, go.Figure)
        # Should have an annotation indicating no data
        assert len(fig.layout.annotations) > 0
        assert "No data available" in fig.layout.annotations[0].text
    
    def test_create_timeline_with_data(self, sample_strava_activities):
        """Test creating timeline with actual data."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_timeline(sample_strava_activities)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0  # Should have traces
        
        # Check that we have different activity types
        activity_types = [trace.name for trace in fig.data]
        expected_types = {"Run", "Ride", "Swim"}
        assert set(activity_types) == expected_types
        
        # Verify layout
        assert fig.layout.title.text == "Activity Timeline"
        assert fig.layout.xaxis.title.text == "Date"
        assert fig.layout.yaxis.title.text == "Activity Type"
    
    def test_create_dashboard_empty_data(self):
        """Test creating dashboard with empty data."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_dashboard([])
        
        assert isinstance(fig, go.Figure)
        # Should have an annotation indicating no data
        assert len(fig.layout.annotations) > 0
        assert "No data available" in fig.layout.annotations[0].text
    
    def test_create_dashboard_with_data(self, sample_strava_activities):
        """Test creating dashboard with actual data."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_dashboard(sample_strava_activities)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0  # Should have multiple traces
        
        # Check layout
        assert fig.layout.title.text == "Activity Dashboard"
        assert fig.layout.height == 800
        
        # Should have subplots (traces for different chart types)
        # We expect at least traces for scatter plot, histogram, pie chart, and bar chart
        assert len(fig.data) >= 4
    
    def test_create_activity_heatmap_empty_data(self):
        """Test creating heatmap with empty data."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_activity_heatmap([])
        
        assert isinstance(fig, go.Figure)
        # Should have an annotation indicating no data
        assert len(fig.layout.annotations) > 0
        assert "No data available" in fig.layout.annotations[0].text
    
    def test_create_activity_heatmap_with_data(self, sample_strava_activities):
        """Test creating heatmap with actual data."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_activity_heatmap(sample_strava_activities)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1  # Should have one heatmap trace
        assert isinstance(fig.data[0], go.Heatmap)
        
        # Check layout
        assert fig.layout.title.text == "Activity Heatmap by Day and Hour"
        assert fig.layout.xaxis.title.text == "Hour of Day"
        assert fig.layout.yaxis.title.text == "Day of Week"
        assert fig.layout.height == 400
    
    def test_to_dataframe(self, sample_strava_activities):
        """Test converting data points to DataFrame."""
        visualizer = PlotlyVisualizer()
        df = visualizer._to_dataframe(sample_strava_activities)
        
        assert len(df) == len(sample_strava_activities)
        
        # Check required columns exist
        required_columns = ['timestamp', 'source', 'data_type']
        for col in required_columns:
            assert col in df.columns
        
        # Check Strava-specific columns exist
        strava_columns = ['activity_id', 'name', 'activity_type', 'distance']
        for col in strava_columns:
            assert col in df.columns
        
        # Verify data types
        assert df['activity_id'].dtype == 'int64'
        assert df['distance'].dtype == 'float64'
        assert df['activity_type'].dtype == 'object'
    
    def test_to_dataframe_mixed_data(self, sample_data_points, sample_strava_activities):
        """Test converting mixed data types to DataFrame."""
        visualizer = PlotlyVisualizer()
        
        # Combine different data types
        mixed_data = sample_data_points + sample_strava_activities
        df = visualizer._to_dataframe(mixed_data)
        
        assert len(df) == len(mixed_data)
        
        # Should handle both DataPoint and StravaActivity objects
        sources = df['source'].unique()
        assert 'test_source' in sources
        assert 'another_source' in sources
        assert 'strava' in sources
    
    def test_to_dataframe_empty_data(self):
        """Test converting empty data to DataFrame."""
        visualizer = PlotlyVisualizer()
        df = visualizer._to_dataframe([])
        
        assert len(df) == 0
        assert isinstance(df, type(visualizer._to_dataframe([sample_data_points[0] for sample_data_points in [[]]])))
    
    def test_to_html(self, sample_strava_activities):
        """Test converting figure to HTML."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_timeline(sample_strava_activities)
        
        html = visualizer.to_html(fig)
        
        assert isinstance(html, str)
        assert "<html>" in html
        assert "<div" in html  # Plotly div
        assert "plotly" in html.lower()
    
    def test_to_html_with_custom_plotlyjs(self, sample_strava_activities):
        """Test converting figure to HTML with custom plotly.js inclusion."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_timeline(sample_strava_activities)
        
        html = visualizer.to_html(fig, include_plotlyjs='inline')
        
        assert isinstance(html, str)
        assert "<html>" in html
        # With inline, the plotly.js should be included in the HTML
        assert len(html) > 50000  # Inline plotly.js makes HTML much larger
    
    def test_timeline_data_ordering(self, sample_strava_activities):
        """Test that timeline respects data ordering."""
        visualizer = PlotlyVisualizer()
        
        # Reverse the order of activities
        reversed_activities = list(reversed(sample_strava_activities))
        fig = visualizer.create_timeline(reversed_activities)
        
        # Should still create a valid figure regardless of input order
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_dashboard_handles_single_activity_type(self):
        """Test dashboard with only one activity type."""
        from little_big_data.models.strava import StravaActivity
        
        # Create activities of only one type
        single_type_activities = [
            StravaActivity(
                timestamp=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
                activity_id=1,
                name=f"Run {i}",
                activity_type="Run",
                distance=5000.0,
                moving_time=1800,
                elapsed_time=1900,
                total_elevation_gain=50.0,
                metadata={"id": i}
            )
            for i in range(1, 4)
        ]
        
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_dashboard(single_type_activities)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
    
    def test_heatmap_data_aggregation(self, sample_strava_activities):
        """Test that heatmap correctly aggregates data by day and hour."""
        visualizer = PlotlyVisualizer()
        fig = visualizer.create_activity_heatmap(sample_strava_activities)
        
        assert isinstance(fig, go.Figure)
        heatmap_trace = fig.data[0]
        
        # Check that we have proper day ordering
        expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        y_labels = list(heatmap_trace.y)
        
        # Should have some subset of the expected days
        for day in y_labels:
            assert day in expected_days
    
    def test_visualizer_with_data_containing_nulls(self):
        """Test visualizer handles data with null/None values gracefully."""
        from little_big_data.models.strava import StravaActivity
        
        activities_with_nulls = [
            StravaActivity(
                timestamp=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
                activity_id=1,
                name="Activity with nulls",
                activity_type="Run",
                distance=5000.0,
                moving_time=1800,
                elapsed_time=1900,
                total_elevation_gain=50.0,
                average_speed=None,  # Null value
                max_speed=None,     # Null value
                calories=None,      # Null value
                metadata={"id": 1}
            )
        ]
        
        visualizer = PlotlyVisualizer()
        
        # Should not raise exceptions
        timeline_fig = visualizer.create_timeline(activities_with_nulls)
        dashboard_fig = visualizer.create_dashboard(activities_with_nulls)
        heatmap_fig = visualizer.create_activity_heatmap(activities_with_nulls)
        
        assert isinstance(timeline_fig, go.Figure)
        assert isinstance(dashboard_fig, go.Figure)
        assert isinstance(heatmap_fig, go.Figure) 