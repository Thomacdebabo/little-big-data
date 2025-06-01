# Setup Guide

## Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and setup the project**:
   ```bash
   cd little-big-data
   uv sync
   ```

3. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate  # On Windows
   ```

## Configuration

1. **Copy the example config**:
   ```bash
   cp config.env.example .env
   ```

2. **Set up Strava API** (optional, for Strava integration):
   - Go to https://www.strava.com/settings/api
   - Create a new application
   - Copy the Client ID and Client Secret to your `.env` file
   - For access token, you can use the OAuth flow through the web interface

## Running the Application

1. **Start the server**:
   ```bash
   python main.py
   ```

2. **Open your browser** and go to:
   ```
   http://localhost:8000
   ```

3. **Explore the API documentation**:
   ```
   http://localhost:8000/docs
   ```

## Usage Examples

### 1. Fetch Strava Data

Using the web interface:
1. Go to http://localhost:8000
2. Click on "Fetch Strava Data" or go to http://localhost:8000/docs
3. Use the `/data/strava/fetch` endpoint with your access token

Using curl:
```bash
curl -X POST "http://localhost:8000/data/strava/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your_strava_access_token",
    "days_back": 30
  }'
```

### 2. View Data

- **Data Summary**: http://localhost:8000/data/summary
- **Browse Data**: http://localhost:8000/data
- **Timeline**: http://localhost:8000/visualizations/timeline
- **Dashboard**: http://localhost:8000/visualizations/dashboard

### 3. Strava OAuth Flow

1. Get authorization URL:
   ```bash
   curl "http://localhost:8000/auth/strava/url?client_id=YOUR_CLIENT_ID"
   ```

2. Visit the returned URL and authorize the app

3. Exchange the code for tokens:
   ```bash
   curl -X POST "http://localhost:8000/auth/strava/token" \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET",
       "code": "AUTHORIZATION_CODE"
     }'
   ```

## Testing

The project includes a comprehensive test suite with both unit and integration tests.

### Install Test Dependencies

```bash
uv sync --group dev
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=little_big_data --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests  
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_core.py

# Run with verbose output
pytest -v
```

### Test Structure

- **`tests/unit/`**: Unit tests for individual components
  - `test_core.py`: Core data models and base classes
  - `test_storage.py`: Storage implementations
  - `test_sources.py`: Data sources (with mocked APIs)
  - `test_visualization.py`: Visualization components

- **`tests/integration/`**: Integration tests for workflows
  - `test_api.py`: API endpoints and HTTP interactions
  - `test_workflows.py`: End-to-end workflows (fetch → store → visualize)

See `tests/README.md` for detailed testing documentation.

## CLI Tool

Install CLI dependencies:
```bash
uv sync --group cli
```

Available commands:
```bash
# Start the web server
python cli.py run

# Show data status
python cli.py status

# Fetch Strava data
python cli.py fetch-strava --access-token YOUR_TOKEN --days 30

# Clear all data
python cli.py clear-data

# Export data to JSON
python cli.py export-data --output-file export.json
```

## Project Structure

```
little-big-data/
├── little_big_data/
│   ├── core/           # Base abstractions and interfaces
│   ├── sources/        # Data source implementations
│   ├── storage/        # Storage backends
│   ├── models/         # Pydantic data models
│   ├── visualization/  # Visualization components
│   └── api/           # FastAPI web interface
├── tests/             # Test suite
│   ├── unit/         # Unit tests
│   ├── integration/  # Integration tests
│   └── conftest.py   # Test fixtures
├── data/              # Local data storage (created automatically)
├── main.py           # Application entry point
├── cli.py            # Command-line interface
├── pyproject.toml    # Project configuration
└── README.md         # Project overview
```

## Adding New Data Sources

To add a new data source, implement the `DataSource` abstract class:

```python
from little_big_data.core.base import DataSource, DataPoint

class MyDataSource(DataSource):
    async def authenticate(self) -> bool:
        # Implement authentication logic
        pass
    
    async def fetch_data(self, start_date=None, end_date=None) -> List[DataPoint]:
        # Implement data fetching logic
        pass
    
    def get_supported_data_types(self) -> List[str]:
        return ["my_data_type"]
```

## Development

### Run with auto-reload
```bash
python main.py
```

### Code Quality
```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy little_big_data/
```

### Pre-commit Checks
Before committing code, run:
```bash
# Format, lint, and test
black .
ruff check . --fix
pytest
``` 