"""Base classes and interfaces for the framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar
from datetime import datetime
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class DataPoint(BaseModel):
    """Base class for all data points."""
    
    timestamp: datetime
    source: str
    data_type: str
    metadata: Dict[str, Any] = {}


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the data source."""
        pass
    
    @abstractmethod
    async def fetch_data(self, start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> List[DataPoint]:
        """Fetch data from the source."""
        pass
    
    @abstractmethod
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types."""
        pass


class DataStorage(ABC):
    """Abstract base class for data storage."""
    
    @abstractmethod
    async def save(self, data_points: List[DataPoint]) -> None:
        """Save data points to storage."""
        pass
    
    @abstractmethod
    async def load(self, source: Optional[str] = None, 
                  data_type: Optional[str] = None,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[DataPoint]:
        """Load data points from storage."""
        pass
    
    @abstractmethod
    async def delete(self, source: Optional[str] = None, 
                    data_type: Optional[str] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> int:
        """Delete data points from storage. Returns count of deleted items."""
        pass


class DataProcessor(Protocol):
    """Protocol for data processors."""
    
    def process(self, data_points: List[DataPoint]) -> List[DataPoint]:
        """Process and transform data points."""
        ...


class Visualizer(ABC):
    """Abstract base class for visualizers."""
    
    @abstractmethod
    def create_timeline(self, data_points: List[DataPoint]) -> Any:
        """Create a timeline visualization."""
        pass
    
    @abstractmethod
    def create_dashboard(self, data_points: List[DataPoint]) -> Any:
        """Create a dashboard visualization."""
        pass 