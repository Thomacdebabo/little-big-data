"""JSON file-based storage implementation."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core.base import DataPoint, DataStorage


class JsonStorage(DataStorage):
    """JSON file-based storage implementation."""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def _get_file_path(self, source: str, data_type: str) -> Path:
        """Get the file path for a specific source and data type."""
        return self.base_path / f"{source}_{data_type}.json"
    
    def _deserialize_point(self, item: dict) -> DataPoint:
        """Deserialize a JSON item back to the appropriate DataPoint subclass."""
        source = item.get('source')
        data_type = item.get('data_type')
        
        # Import here to avoid circular imports
        if source == 'strava' and data_type == 'activity':
            from ..models.strava import StravaActivity
            return StravaActivity.model_validate(item)
        else:
            return DataPoint.model_validate(item)
    
    async def save(self, data_points: List[DataPoint]) -> None:
        """Save data points to JSON files, organized by source and data_type."""
        # Group data points by source and data_type
        groups: dict[tuple[str, str], List[DataPoint]] = {}
        
        for point in data_points:
            key = (point.source, point.data_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(point)
        
        # Save each group to its corresponding file
        for (source, data_type), points in groups.items():
            file_path = self._get_file_path(source, data_type)
            
            # Load existing data if file exists
            existing_data = []
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    # Handle corrupted files by treating as empty
                    existing_data = []
            
            # Convert existing data back to DataPoint objects for deduplication
            existing_points = [self._deserialize_point(item) for item in existing_data]
            
            # Create a set of existing timestamps + IDs for deduplication
            existing_ids = set()
            for point in existing_points:
                # Use timestamp + metadata for simple deduplication
                point_id = (point.timestamp.isoformat(), 
                           point.metadata.get('id', str(hash(str(point.metadata)))))
                existing_ids.add(point_id)
            
            # Filter out duplicates from new points
            new_points = []
            for point in points:
                point_id = (point.timestamp.isoformat(), 
                           point.metadata.get('id', str(hash(str(point.metadata)))))
                if point_id not in existing_ids:
                    new_points.append(point)
            
            # Combine and sort by timestamp
            all_points = existing_points + new_points
            all_points.sort(key=lambda x: x.timestamp)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump([point.model_dump() for point in all_points], f, 
                         indent=2, default=str)
    
    async def load(self, source: Optional[str] = None, 
                  data_type: Optional[str] = None,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[DataPoint]:
        """Load data points from JSON files."""
        data_points = []
        
        # Determine which files to load
        if source and data_type:
            files_to_load = [self._get_file_path(source, data_type)]
        else:
            # Load all files that match the criteria
            files_to_load = []
            for file_path in self.base_path.glob("*.json"):
                # Skip files that don't follow the source_datatype.json pattern
                if "_" not in file_path.stem:
                    continue
                try:
                    file_source, file_data_type = file_path.stem.split("_", 1)
                    if (source is None or file_source == source) and \
                       (data_type is None or file_data_type == data_type):
                        files_to_load.append(file_path)
                except ValueError:
                    # Skip files with unexpected naming
                    continue
        
        # Load data from files
        for file_path in files_to_load:
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        file_data = json.load(f)
                        for item in file_data:
                            point = self._deserialize_point(item)
                            # Apply date filters
                            if start_date and point.timestamp < start_date:
                                continue
                            if end_date and point.timestamp > end_date:
                                continue
                            data_points.append(point)
                except json.JSONDecodeError:
                    # Skip corrupted files
                    continue
        
        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)
        return data_points
    
    async def delete(self, source: Optional[str] = None, 
                    data_type: Optional[str] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> int:
        """Delete data points from storage."""
        deleted_count = 0
        
        # Load all matching data
        data_points = await self.load(source, data_type, start_date, end_date)
        
        if not data_points:
            return 0
        
        # If deleting all data for specific source/data_type, just remove the file
        if source and data_type and start_date is None and end_date is None:
            file_path = self._get_file_path(source, data_type)
            if file_path.exists():
                deleted_count = len(data_points)
                file_path.unlink()
        else:
            # Load all data and filter out what should be deleted
            all_data = await self.load()
            remaining_data = []
            
            for point in all_data:
                should_delete = True
                
                # Check if this point matches deletion criteria
                if source and point.source != source:
                    should_delete = False
                if data_type and point.data_type != data_type:
                    should_delete = False
                if start_date and point.timestamp < start_date:
                    should_delete = False
                if end_date and point.timestamp > end_date:
                    should_delete = False
                
                if should_delete:
                    deleted_count += 1
                else:
                    remaining_data.append(point)
            
            # Clear all files and save remaining data
            for file_path in self.base_path.glob("*.json"):
                file_path.unlink()
            
            if remaining_data:
                await self.save(remaining_data)
        
        return deleted_count 