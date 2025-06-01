"""Unit tests for storage implementations."""

import pytest
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from little_big_data.storage.json_storage import JsonStorage
from little_big_data.core.base import DataPoint


class TestJsonStorage:
    """Test the JsonStorage implementation."""
    
    @pytest.mark.asyncio
    async def test_save_and_load_data_points(self, json_storage, sample_data_points):
        """Test saving and loading data points."""
        # Save data points
        await json_storage.save(sample_data_points)
        
        # Load all data
        loaded_points = await json_storage.load()
        
        assert len(loaded_points) == len(sample_data_points)
        
        # Check that data is sorted by timestamp
        timestamps = [point.timestamp for point in loaded_points]
        assert timestamps == sorted(timestamps)
    
    @pytest.mark.asyncio
    async def test_save_creates_correct_files(self, json_storage, sample_data_points):
        """Test that saving creates the correct files."""
        await json_storage.save(sample_data_points)
        
        # Check that files were created
        expected_files = {
            "test_source_test_type.json",
            "another_source_another_type.json"
        }
        
        actual_files = {f.name for f in json_storage.base_path.glob("*.json")}
        assert actual_files == expected_files
    
    @pytest.mark.asyncio
    async def test_load_with_source_filter(self, json_storage, sample_data_points):
        """Test loading with source filter."""
        await json_storage.save(sample_data_points)
        
        # Load only test_source data
        loaded_points = await json_storage.load(source="test_source")
        
        assert len(loaded_points) == 2
        assert all(point.source == "test_source" for point in loaded_points)
    
    @pytest.mark.asyncio
    async def test_load_with_data_type_filter(self, json_storage, sample_data_points):
        """Test loading with data type filter."""
        await json_storage.save(sample_data_points)
        
        # Load only test_type data
        loaded_points = await json_storage.load(data_type="test_type")
        
        assert len(loaded_points) == 2
        assert all(point.data_type == "test_type" for point in loaded_points)
    
    @pytest.mark.asyncio
    async def test_load_with_date_filter(self, json_storage, sample_data_points):
        """Test loading with date filters."""
        await json_storage.save(sample_data_points)
        
        # Load data from specific date range
        start_date = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        
        loaded_points = await json_storage.load(start_date=start_date, end_date=end_date)
        
        assert len(loaded_points) == 2
        for point in loaded_points:
            assert start_date <= point.timestamp <= end_date
    
    @pytest.mark.asyncio
    async def test_load_with_combined_filters(self, json_storage, sample_data_points):
        """Test loading with multiple filters combined."""
        await json_storage.save(sample_data_points)
        
        # Load test_source data from specific date
        start_date = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        
        loaded_points = await json_storage.load(
            source="test_source",
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(loaded_points) == 2
        assert all(point.source == "test_source" for point in loaded_points)
        for point in loaded_points:
            assert start_date <= point.timestamp <= end_date
    
    @pytest.mark.asyncio
    async def test_deduplication(self, json_storage, sample_data_points):
        """Test that duplicate data points are not saved."""
        # Save data points twice
        await json_storage.save(sample_data_points)
        await json_storage.save(sample_data_points)
        
        # Should still only have 3 unique points
        loaded_points = await json_storage.load()
        assert len(loaded_points) == 3
    
    @pytest.mark.asyncio
    async def test_delete_all_data(self, json_storage, sample_data_points):
        """Test deleting all data."""
        await json_storage.save(sample_data_points)
        
        # Delete all data
        deleted_count = await json_storage.delete()
        
        assert deleted_count == 3
        
        # Verify no data remains
        loaded_points = await json_storage.load()
        assert len(loaded_points) == 0
    
    @pytest.mark.asyncio
    async def test_delete_by_source(self, json_storage, sample_data_points):
        """Test deleting data by source."""
        await json_storage.save(sample_data_points)
        
        # Delete only test_source data
        deleted_count = await json_storage.delete(source="test_source")
        
        assert deleted_count == 2
        
        # Verify only another_source data remains
        loaded_points = await json_storage.load()
        assert len(loaded_points) == 1
        assert loaded_points[0].source == "another_source"
    
    @pytest.mark.asyncio
    async def test_delete_by_data_type(self, json_storage, sample_data_points):
        """Test deleting data by data type."""
        await json_storage.save(sample_data_points)
        
        # Delete only test_type data
        deleted_count = await json_storage.delete(data_type="test_type")
        
        assert deleted_count == 2
        
        # Verify only another_type data remains
        loaded_points = await json_storage.load()
        assert len(loaded_points) == 1
        assert loaded_points[0].data_type == "another_type"
    
    @pytest.mark.asyncio
    async def test_delete_specific_source_and_type(self, json_storage, sample_data_points):
        """Test deleting data by both source and data type."""
        await json_storage.save(sample_data_points)
        
        # Delete test_source test_type data (should remove the file)
        deleted_count = await json_storage.delete(source="test_source", data_type="test_type")
        
        assert deleted_count == 2
        
        # Verify file was removed
        test_file = json_storage.base_path / "test_source_test_type.json"
        assert not test_file.exists()
        
        # Verify other data remains
        loaded_points = await json_storage.load()
        assert len(loaded_points) == 1
    
    @pytest.mark.asyncio
    async def test_delete_with_date_range(self, json_storage, sample_data_points):
        """Test deleting data within a date range."""
        await json_storage.save(sample_data_points)
        
        # Delete data from first two days
        start_date = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, 23, 59, 59, tzinfo=timezone.utc)
        
        deleted_count = await json_storage.delete(start_date=start_date, end_date=end_date)
        
        assert deleted_count == 2
        
        # Verify only the third data point remains
        loaded_points = await json_storage.load()
        assert len(loaded_points) == 1
        assert loaded_points[0].timestamp.day == 3
    
    @pytest.mark.asyncio
    async def test_empty_storage_operations(self, json_storage):
        """Test operations on empty storage."""
        # Load from empty storage
        loaded_points = await json_storage.load()
        assert len(loaded_points) == 0
        
        # Delete from empty storage
        deleted_count = await json_storage.delete()
        assert deleted_count == 0
    
    @pytest.mark.asyncio
    async def test_file_path_generation(self, json_storage):
        """Test that file paths are generated correctly."""
        path1 = json_storage._get_file_path("source1", "type1")
        path2 = json_storage._get_file_path("source2", "type2")
        
        assert path1.name == "source1_type1.json"
        assert path2.name == "source2_type2.json"
        assert path1.parent == json_storage.base_path
        assert path2.parent == json_storage.base_path
    
    @pytest.mark.asyncio
    async def test_data_persistence_across_instances(self, temp_dir, sample_data_points):
        """Test that data persists across storage instances."""
        # Save data with first instance
        storage1 = JsonStorage(base_path=str(temp_dir))
        await storage1.save(sample_data_points)
        
        # Load data with second instance
        storage2 = JsonStorage(base_path=str(temp_dir))
        loaded_points = await storage2.load()
        
        assert len(loaded_points) == len(sample_data_points)
    
    @pytest.mark.asyncio
    async def test_concurrent_saves(self, json_storage):
        """Test concurrent save operations."""
        # Create different data points
        points1 = [DataPoint(
            timestamp=datetime.now(timezone.utc),
            source="source1",
            data_type="type1",
            metadata={"id": "1"}
        )]
        
        points2 = [DataPoint(
            timestamp=datetime.now(timezone.utc),
            source="source2",
            data_type="type2",
            metadata={"id": "2"}
        )]
        
        # Save concurrently
        import asyncio
        await asyncio.gather(
            json_storage.save(points1),
            json_storage.save(points2)
        )
        
        # Verify both were saved
        all_points = await json_storage.load()
        assert len(all_points) == 2
        
        sources = {point.source for point in all_points}
        assert sources == {"source1", "source2"} 