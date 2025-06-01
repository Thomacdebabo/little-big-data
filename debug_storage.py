import asyncio
from little_big_data.storage.json_storage import JsonStorage
from little_big_data.core.base import DataPoint
from datetime import datetime, timezone
import tempfile
import shutil
from pathlib import Path

async def test():
    temp_path = tempfile.mkdtemp()
    storage = JsonStorage(base_path=temp_path)
    
    data = [
        DataPoint(
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            source='test_source',
            data_type='test_type',
            metadata={'id': '1', 'value': 10}
        ),
        DataPoint(
            timestamp=datetime(2024, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
            source='test_source',
            data_type='test_type',
            metadata={'id': '2', 'value': 20}
        ),
        DataPoint(
            timestamp=datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            source='another_source',
            data_type='another_type',
            metadata={'id': '3', 'value': 30}
        ),
    ]
    
    await storage.save(data)
    
    # List files created
    print('Files created:')
    for f in Path(temp_path).glob('*.json'):
        print(f'  {f.name}')
    
    # Try loading all
    all_data = await storage.load()
    print(f'All results: {len(all_data)}')
    
    # Try loading with filter
    filtered = await storage.load(source='test_source')
    print(f'Filtered results: {len(filtered)}')
    for point in filtered:
        print(f'  {point.source} / {point.data_type}')
    
    shutil.rmtree(temp_path)

if __name__ == "__main__":
    asyncio.run(test()) 