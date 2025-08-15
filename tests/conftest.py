"""Test configuration and fixtures for OpenProject MCP Server tests."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_openproject_response():
    """Standard mock response for OpenProject API."""
    return {
        "_embedded": {
            "elements": []
        },
        "total": 0,
        "_links": {
            "self": {"href": "/api/v3/test"}
        }
    }


@pytest.fixture
def mock_work_package():
    """Mock work package data."""
    return {
        "id": 123,
        "subject": "Test Work Package",
        "description": {"raw": "Test description"},
        "startDate": "2024-01-01",
        "dueDate": "2024-01-31",
        "estimatedTime": "PT8H",
        "_links": {
            "project": {
                "href": "/api/v3/projects/1",
                "title": "Test Project"
            },
            "status": {
                "href": "/api/v3/statuses/1",
                "title": "New"
            },
            "type": {
                "href": "/api/v3/types/1",
                "title": "Task"
            },
            "priority": {
                "href": "/api/v3/priorities/2",
                "title": "Normal"
            },
            "assignee": {
                "href": "/api/v3/users/1",
                "title": "John Doe"
            }
        }
    }


@pytest.fixture
def mock_project():
    """Mock project data."""
    return {
        "id": 1,
        "name": "Test Project",
        "identifier": "test-project",
        "description": {"raw": "Test project description"},
        "status": "active",
        "_links": {
            "self": {"href": "/api/v3/projects/1"}
        }
    }


@pytest.fixture
def mock_user():
    """Mock user data."""
    return {
        "id": 1,
        "name": "John Doe",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "login": "john.doe",
        "status": "active",
        "admin": False,
        "createdAt": "2024-01-01T00:00:00Z",
        "_links": {
            "self": {"href": "/api/v3/users/1"}
        }
    }


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    class MockSettings:
        openproject_url = "https://test.openproject.com"
        openproject_api_key = "test_api_key"
    
    return MockSettings()


@pytest.fixture(autouse=True)
def mock_config(monkeypatch, mock_settings):
    """Mock the settings configuration."""
    import src.config
    monkeypatch.setattr(src.config, 'settings', mock_settings)


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger
