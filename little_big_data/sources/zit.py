"""Zit data source implementation."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..core.base import DataSource, DataPoint

try:
    from zit.storage import Storage, SubtaskStorage
    from zit.events import Project, Subtask, GitCommit
    from zit.calculate import calculate_project_times
    from zit.fm.filemanager import ZitFileManager
except ImportError:
    raise ImportError("Zit package is required. Install it with 'uv sync'")


class ZitProjectDataPoint(DataPoint):
    """DataPoint for Zit project events."""
    
    def __init__(self, project: Project, **kwargs):
        super().__init__(
            timestamp=project.timestamp,
            source="zit",
            data_type="project",
            metadata={
                "project_name": project.name,
                "raw_data": project.dict()
            },
            **kwargs
        )


class ZitSubtaskDataPoint(DataPoint):
    """DataPoint for Zit subtask events."""
    
    def __init__(self, subtask: Subtask, **kwargs):
        super().__init__(
            timestamp=subtask.timestamp,
            source="zit",
            data_type="subtask",
            metadata={
                "project_name": subtask.name,
                "note": subtask.note,
                "raw_data": subtask.dict()
            },
            **kwargs
        )


class ZitSource(DataSource):
    """Zit data source for time tracking events."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("zit", config or {})
        self.data_dir = Path.home() / '.zit'
        self._authenticated = True  # Zit uses local files, no authentication needed
        # Initialize storage to get excluded projects
        self._storage = Storage()
        self.exclude_projects = self._storage.exclude_projects
    
    async def authenticate(self) -> bool:
        """Check if zit data directory exists."""
        if not self.data_dir.exists():
            self._authenticated = False
            return False
        self._authenticated = True
        return True
    
    async def fetch_data(self, start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> List[DataPoint]:
        """Fetch projects and subtasks from zit storage."""
        if not self._authenticated:
            if not await self.authenticate():
                raise RuntimeError("Zit data directory not found")
        
        data_points = []
        
        # If no date range specified, fetch last 30 days
        if not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        elif not start_date:
            start_date = end_date - timedelta(days=30)
        elif not end_date:
            end_date = datetime.now()
        
        # Get available dates from storage and filter by date range
        available_dates = self.get_available_dates()
        
        for date_str in available_dates:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if start_date.date() <= date_obj.date() <= end_date.date():
                    # Use storage class for this date
                    storage = Storage(date_str)
                    events = storage.get_events()
                    
                    for event in events:
                        # Filter by timestamp and excluded projects
                        if (start_date <= event.timestamp <= end_date and 
                            event.name not in self.exclude_projects):
                            
                            if isinstance(event, Subtask):
                                data_points.append(ZitSubtaskDataPoint(event))
                            else:
                                data_points.append(ZitProjectDataPoint(event))
            except ValueError:
                continue
        
        # Sort by timestamp
        data_points.sort(key=lambda dp: dp.timestamp)
        return data_points
    
    async def fetch_projects_only(self, start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None) -> List[ZitProjectDataPoint]:
        """Fetch only project events (excluding subtasks)."""
        all_data = await self.fetch_data(start_date, end_date)
        return [dp for dp in all_data if dp.data_type == "project"]
    
    async def fetch_subtasks_only(self, start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None) -> List[ZitSubtaskDataPoint]:
        """Fetch only subtask events."""
        all_data = await self.fetch_data(start_date, end_date)
        return [dp for dp in all_data if dp.data_type == "subtask"]
    
    async def get_current_task(self) -> Optional[str]:
        """Get the current active task."""
        return self._storage.get_current_task()
    
    async def get_daily_summary(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get a summary of projects for a specific day using storage's built-in functionality."""
        if not date:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        storage = Storage(date_str)
        
        # Get events for the day
        events = storage.get_events()
        
        project_times, _,_ = calculate_project_times(events, exclude_projects=self.exclude_projects, add_ongoing=False)
        project_times = {k: v for k, v in project_times.items() if k not in self.exclude_projects}
        return {
            "date": date_str,
            "total_projects": len(set(e.name for e in events)),
            "total_events": len(events),
            "project_times": project_times,
            "projects": list(set(e.name for e in events)),
            "excluded_projects": list(self.exclude_projects)
        }
    
    async def get_multi_day_summary(self, start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get a summary across multiple days using storage functionality."""
        if not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        elif not start_date:
            start_date = end_date - timedelta(days=7)
        elif not end_date:
            end_date = datetime.now()
        
        daily_summaries = {}
        total_project_times = {}
        all_projects = set()
        total_events = 0
        
        # Get summaries for each day
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_summary = await self.get_daily_summary(datetime.combine(current_date, datetime.min.time()))
            
            daily_summaries[date_str] = daily_summary
            total_events += daily_summary['total_events']
            all_projects.update(daily_summary['projects'])
            
            # Aggregate project times
            for project, time_spent in daily_summary['project_times'].items():
                if project not in total_project_times:
                    total_project_times[project] = 0
                total_project_times[project] += time_spent
            
            current_date += timedelta(days=1)
        
        return {
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "total_projects": len(all_projects),
            "total_events": total_events,
            "total_project_times": total_project_times,
            "daily_summaries": daily_summaries,
            "excluded_projects": list(self.exclude_projects)
        }
    
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types."""
        return ["project", "subtask"]
    
    def get_available_dates(self) -> List[str]:
        """Get list of available dates with zit data."""
        if not self.data_dir.exists():
            return []
        
        dates = []
        for file_path in self.data_dir.glob("*.csv"):
            if file_path.stem.count('-') == 2:  # Format: YYYY-MM-DD
                try:
                    # Validate date format
                    datetime.strptime(file_path.stem, '%Y-%m-%d')
                    dates.append(file_path.stem)
                except ValueError:
                    continue
        
        return sorted(dates)
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about the zit storage."""
        available_dates = self.get_available_dates()
        
        if not available_dates:
            return {
                "total_days": 0,
                "date_range": None,
                "total_events": 0,
                "unique_projects": 0
            }
        
        # Get first and last dates
        first_date = available_dates[0]
        last_date = available_dates[-1]
        
        # Count total events and unique projects
        all_projects = set()
        total_events = 0
        
        for date_str in available_dates[-30:]:  # Last 30 days for performance
            try:
                storage = Storage(date_str)
                events = storage.get_events()
                filtered_events = [e for e in events if e.name not in self.exclude_projects]
                
                total_events += len(filtered_events)
                all_projects.update(e.name for e in filtered_events)
            except Exception:
                continue
        
        return {
            "total_days": len(available_dates),
            "date_range": {
                "first": first_date,
                "last": last_date
            },
            "recent_events": total_events,  # Last 30 days
            "unique_projects": len(all_projects),
            "excluded_projects": list(self.exclude_projects)
        }
