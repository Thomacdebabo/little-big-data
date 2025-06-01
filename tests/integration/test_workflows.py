"""Integration tests for end-to-end workflows."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from little_big_data.storage.json_storage import JsonStorage
from little_big_data.sources.strava import StravaSource
from little_big_data.visualization.plotly_viz import PlotlyVisualizer


class TestEndToEndWorkflows:
    """Test complete workflows from data fetching to visualization."""
    
    @pytest.mark.asyncio
    async def test_complete_strava_workflow(self, mock_strava_api_responses, temp_dir):
        """Test complete workflow: fetch from Strava, store, and visualize."""
        # 1. Setup components
        storage = JsonStorage(base_path=str(temp_dir))
        visualizer = PlotlyVisualizer()
        
        # 2. Mock Strava API responses
        with patch("httpx.AsyncClient") as mock_client:
            # Mock authentication
            auth_response = MagicMock()
            auth_response.status_code = 200
            auth_response.json.return_value = mock_strava_api_responses["athlete"]
            
            # Mock activities fetch
            activities_response = MagicMock()
            activities_response.status_code = 200
            activities_response.json.return_value = mock_strava_api_responses["activities"]
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                auth_response,
                activities_response
            ]
            
            # 3. Create and authenticate Strava source
            strava_config = {"access_token": "test_token"}
            strava_source = StravaSource(strava_config)
            
            authenticated = await strava_source.authenticate()
            assert authenticated is True
            
            # 4. Fetch data
            start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(2024, 1, 3, tzinfo=timezone.utc)
            
            activities = await strava_source.fetch_data(start_date=start_date, end_date=end_date)
            assert len(activities) == 2
            
            # 5. Store data
            await storage.save(activities)
            
            # 6. Verify data was saved
            stored_activities = await storage.load(source="strava", data_type="activity")
            assert len(stored_activities) == 2
            
            # 7. Create visualizations
            timeline_fig = visualizer.create_timeline(stored_activities)
            dashboard_fig = visualizer.create_dashboard(stored_activities)
            heatmap_fig = visualizer.create_activity_heatmap(stored_activities)
            
            # 8. Verify visualizations were created
            assert timeline_fig is not None
            assert dashboard_fig is not None
            assert heatmap_fig is not None
            
            # 9. Verify we can export to HTML
            timeline_html = visualizer.to_html(timeline_fig)
            assert "Activity Timeline" in timeline_html
            assert "plotly" in timeline_html.lower()
    
    @pytest.mark.asyncio
    async def test_data_persistence_workflow(self, sample_strava_activities, temp_dir):
        """Test data persistence across different storage instances."""
        # 1. Save data with first storage instance
        storage1 = JsonStorage(base_path=str(temp_dir))
        await storage1.save(sample_strava_activities)
        
        # 2. Load data with second storage instance
        storage2 = JsonStorage(base_path=str(temp_dir))
        loaded_activities = await storage2.load()
        
        assert len(loaded_activities) == len(sample_strava_activities)
        
        # 3. Verify data integrity
        original_ids = {act.activity_id for act in sample_strava_activities}
        loaded_ids = {act.metadata.get("id") for act in loaded_activities}
        assert original_ids == loaded_ids
        
        # 4. Add more data with third instance
        storage3 = JsonStorage(base_path=str(temp_dir))
        new_activity = sample_strava_activities[0]
        new_activity.activity_id = 99999  # Different ID to avoid deduplication
        new_activity.metadata["id"] = 99999
        
        await storage3.save([new_activity])
        
        # 5. Verify total count
        all_activities = await storage3.load()
        assert len(all_activities) == len(sample_strava_activities) + 1
    
    @pytest.mark.asyncio
    async def test_data_filtering_workflow(self, temp_dir):
        """Test complex data filtering scenarios."""
        storage = JsonStorage(base_path=str(temp_dir))
        
        # Create test data with different sources and dates
        from little_big_data.core.base import DataPoint
        from little_big_data.models.strava import StravaActivity
        
        test_data = [
            # Strava activities
            StravaActivity(
                timestamp=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                activity_id=1,
                name="Morning Run",
                activity_type="Run",
                distance=5000,
                moving_time=1800,
                elapsed_time=1900,
                total_elevation_gain=50,
                metadata={"id": 1}
            ),
            StravaActivity(
                timestamp=datetime(2024, 1, 2, 18, 0, tzinfo=timezone.utc),
                activity_id=2,
                name="Evening Ride",
                activity_type="Ride",
                distance=25000,
                moving_time=3600,
                elapsed_time=3750,
                total_elevation_gain=200,
                metadata={"id": 2}
            ),
            # Generic data points
            DataPoint(
                timestamp=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
                source="fitbit",
                data_type="steps",
                metadata={"steps": 8000}
            ),
            DataPoint(
                timestamp=datetime(2024, 1, 3, 8, 0, tzinfo=timezone.utc),
                source="fitbit",
                data_type="sleep",
                metadata={"duration": 480}  # 8 hours
            ),
        ]
        
        # Save all data
        await storage.save(test_data)
        
        # Test source filtering
        strava_data = await storage.load(source="strava")
        assert len(strava_data) == 2
        assert all(point.source == "strava" for point in strava_data)
        
        fitbit_data = await storage.load(source="fitbit")
        assert len(fitbit_data) == 2
        assert all(point.source == "fitbit" for point in fitbit_data)
        
        # Test data type filtering
        activities = await storage.load(data_type="activity")
        assert len(activities) == 2
        
        steps_data = await storage.load(data_type="steps")
        assert len(steps_data) == 1
        
        # Test date filtering
        jan_1_data = await storage.load(
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)
        )
        assert len(jan_1_data) == 2  # Morning run + fitbit steps
        
        # Test combined filtering
        strava_jan_1 = await storage.load(
            source="strava",
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)
        )
        assert len(strava_jan_1) == 1
        assert strava_jan_1[0].metadata["id"] == 1
    
    @pytest.mark.asyncio
    async def test_data_deduplication_workflow(self, temp_dir):
        """Test that duplicate data is properly handled."""
        storage = JsonStorage(base_path=str(temp_dir))
        
        from little_big_data.models.strava import StravaActivity
        
        # Create the same activity multiple times
        activity = StravaActivity(
            timestamp=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
            activity_id=12345,
            name="Test Activity",
            activity_type="Run",
            distance=5000,
            moving_time=1800,
            elapsed_time=1900,
            total_elevation_gain=50,
            metadata={"id": 12345}
        )
        
        # Save the same activity multiple times
        for _ in range(3):
            await storage.save([activity])
        
        # Should only have one copy
        activities = await storage.load()
        assert len(activities) == 1
        assert activities[0].activity_id == 12345
    
    @pytest.mark.asyncio
    async def test_visualization_workflow_with_mixed_data(self, temp_dir):
        """Test visualization with mixed data types."""
        storage = JsonStorage(base_path=str(temp_dir))
        visualizer = PlotlyVisualizer()
        
        # Create mixed data
        from little_big_data.core.base import DataPoint
        from little_big_data.models.strava import StravaActivity
        
        mixed_data = [
            StravaActivity(
                timestamp=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
                activity_id=1,
                name="Morning Run",
                activity_type="Run",
                distance=5000,
                moving_time=1800,
                elapsed_time=1900,
                total_elevation_gain=50,
                metadata={"id": 1}
            ),
            DataPoint(
                timestamp=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
                source="custom",
                data_type="measurement",
                metadata={"value": 42}
            ),
        ]
        
        await storage.save(mixed_data)
        
        # Load all data
        all_data = await storage.load()
        
        # Create visualizations - should handle mixed data gracefully
        timeline_fig = visualizer.create_timeline(all_data)
        dashboard_fig = visualizer.create_dashboard(all_data)
        
        assert timeline_fig is not None
        assert dashboard_fig is not None
        
        # Timeline should show both data types
        assert len(timeline_fig.data) >= 1  # At least one trace (may be grouped by activity type)
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, temp_dir):
        """Test system behavior when errors occur."""
        storage = JsonStorage(base_path=str(temp_dir))
        
        # Test saving with invalid data
        from little_big_data.core.base import DataPoint
        
        valid_data = DataPoint(
            timestamp=datetime.now(timezone.utc),
            source="test",
            data_type="test",
            metadata={"id": 1}
        )
        
        # This should work
        await storage.save([valid_data])
        loaded = await storage.load()
        assert len(loaded) == 1
        
        # Test loading from corrupted file
        corrupt_file = storage.base_path / "corrupt_data.json"
        corrupt_file.write_text("invalid json {")
        
        # Should still load valid files despite corrupted one
        loaded = await storage.load()
        assert len(loaded) == 1  # Should still get the valid data
    
    @pytest.mark.asyncio
    async def test_large_dataset_workflow(self, temp_dir):
        """Test workflow with larger dataset."""
        storage = JsonStorage(base_path=str(temp_dir))
        visualizer = PlotlyVisualizer()
        
        from little_big_data.models.strava import StravaActivity
        
        # Create 100 activities over 100 days
        large_dataset = []
        base_date = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
        
        for i in range(100):
            activity = StravaActivity(
                timestamp=base_date + timedelta(days=i),
                activity_id=i + 1,
                name=f"Activity {i + 1}",
                activity_type="Run" if i % 2 == 0 else "Ride",
                distance=5000 + (i * 100),
                moving_time=1800 + (i * 10),
                elapsed_time=1900 + (i * 10),
                total_elevation_gain=50 + i,
                metadata={"id": i + 1}
            )
            large_dataset.append(activity)
        
        # Save in batches to simulate real usage
        batch_size = 20
        for i in range(0, len(large_dataset), batch_size):
            batch = large_dataset[i:i + batch_size]
            await storage.save(batch)
        
        # Verify all data was saved
        all_data = await storage.load()
        assert len(all_data) == 100
        
        # Test filtering on large dataset
        runs_only = await storage.load(source="strava")
        assert len(runs_only) == 100
        
        # Test date range filtering
        first_month = await storage.load(
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)  # Include the full last day
        )
        assert len(first_month) == 31
        
        # Create visualizations with large dataset
        timeline_fig = visualizer.create_timeline(all_data[:20])  # Use subset for performance
        dashboard_fig = visualizer.create_dashboard(all_data[:20])
        
        assert timeline_fig is not None
        assert dashboard_fig is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_access_workflow(self, temp_dir):
        """Test concurrent access to storage."""
        import asyncio
        
        # Create multiple storage instances
        storages = [JsonStorage(base_path=str(temp_dir)) for _ in range(3)]
        
        from little_big_data.core.base import DataPoint
        
        async def save_data(storage_instance, source_id):
            """Save data with a specific storage instance."""
            data = [
                DataPoint(
                    timestamp=datetime.now(timezone.utc),
                    source=f"source_{source_id}",
                    data_type="test",
                    metadata={"id": f"{source_id}_{i}"}
                )
                for i in range(5)
            ]
            await storage_instance.save(data)
        
        # Save data concurrently
        await asyncio.gather(*[
            save_data(storage, i) for i, storage in enumerate(storages)
        ])
        
        # Verify all data was saved
        final_storage = JsonStorage(base_path=str(temp_dir))
        all_data = await final_storage.load()
        
        # Should have 3 sources × 5 items = 15 total items
        assert len(all_data) == 15
        
        # Verify we have all 3 sources
        sources = {point.source for point in all_data}
        expected_sources = {"source_0", "source_1", "source_2"}
        assert sources == expected_sources 