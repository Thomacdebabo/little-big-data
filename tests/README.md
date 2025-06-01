# Testing Framework

This directory contains the test suite for Little Big Data. The tests are organized into unit tests and integration tests to ensure code quality and functionality.

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Unit tests for individual components
│   ├── test_core.py     # Core abstractions and models
│   ├── test_storage.py  # Storage implementations
│   ├── test_sources.py  # Data sources (with mocked APIs)
│   └── test_visualization.py # Visualization components
├── integration/         # Integration tests for workflows
│   ├── test_api.py      # API endpoints
│   └── test_workflows.py # End-to-end workflows
└── README.md           # This file
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
uv sync --group dev
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=little_big_data --cov-report=html

# Run tests with verbose output
pytest -v
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests by marker
pytest -m unit
pytest -m integration
```

### Run Specific Test Files

```bash
# Test core functionality
pytest tests/unit/test_core.py

# Test storage
pytest tests/unit/test_storage.py

# Test API endpoints
pytest tests/integration/test_api.py
```

### Run Tests with Different Options

```bash
# Stop on first failure
pytest -x

# Show local variables in tracebacks
pytest -l

# Run tests in parallel (if pytest-xdist is installed)
pytest -n auto

# Run only failed tests from last run
pytest --lf
```

## Test Categories

### Unit Tests (`tests/unit/`)

Test individual components in isolation:

- **`test_core.py`**: Tests for base classes (DataPoint, StravaActivity, etc.)
- **`test_storage.py`**: Tests for storage implementations (JsonStorage)
- **`test_sources.py`**: Tests for data sources (StravaSource with mocked APIs)
- **`test_visualization.py`**: Tests for visualization components (PlotlyVisualizer)

### Integration Tests (`tests/integration/`)

Test component interactions and workflows:

- **`test_api.py`**: Tests for FastAPI endpoints and HTTP interactions
- **`test_workflows.py`**: End-to-end workflow tests (fetch → store → visualize)

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `temp_dir`: Temporary directory for file operations
- `json_storage`: JsonStorage instance with temp directory
- `sample_data_points`: Generic test data points
- `sample_strava_activities`: Sample Strava activities
- `api_client`: FastAPI test client
- `mock_strava_api_responses`: Mock API responses for testing

## Mocking Strategy

- **External APIs**: Strava API calls are mocked using `unittest.mock`
- **File System**: Tests use temporary directories for isolation
- **HTTP Clients**: `httpx.AsyncClient` is mocked for API tests
- **Time**: `freezegun` can be used for datetime mocking if needed

## Writing New Tests

### Unit Test Example

```python
import pytest
from little_big_data.core.base import DataPoint

def test_my_function():
    """Test description."""
    # Arrange
    data_point = DataPoint(...)
    
    # Act
    result = my_function(data_point)
    
    # Assert
    assert result == expected_value
```

### Async Test Example

```python
@pytest.mark.asyncio
async def test_async_function(json_storage):
    """Test async functionality."""
    # Arrange
    test_data = [...]
    
    # Act
    await json_storage.save(test_data)
    result = await json_storage.load()
    
    # Assert
    assert len(result) == len(test_data)
```

### API Test Example

```python
def test_api_endpoint(api_client):
    """Test API endpoint."""
    # Act
    response = api_client.get("/endpoint")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

## Coverage Goals

While we don't aim for 100% coverage, we focus on testing:

- ✅ Critical business logic
- ✅ Data processing and storage
- ✅ API endpoints and error handling
- ✅ Core data models and validation
- ✅ Integration workflows

Areas with lower priority for testing:
- CLI output formatting
- HTML template rendering details
- Third-party library wrapper code

## Continuous Integration

Tests are designed to run in CI environments:

- No external dependencies (APIs are mocked)
- Temporary file cleanup
- Deterministic test data
- Fast execution times

## Debugging Tests

```bash
# Run with pdb debugger
pytest --pdb

# Show print statements
pytest -s

# Run specific test with full output
pytest tests/unit/test_core.py::TestDataPoint::test_create_data_point -v -s
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Test names should describe what is being tested
3. **AAA Pattern**: Arrange, Act, Assert structure
4. **Mock External Dependencies**: Don't make real API calls or write to production paths
5. **Use Fixtures**: Leverage pytest fixtures for common setup
6. **Test Edge Cases**: Include tests for error conditions and edge cases 