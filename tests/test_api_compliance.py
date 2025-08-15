"""API compliance tests for OpenProject MCP Server."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from src.openproject_client import OpenProjectClient, OpenProjectAPIError
from src.models import WorkPackageCreateRequest, WorkPackageRelationCreateRequest
from pydantic import ValidationError


class TestAPICompliance:
    """Test OpenProject API compliance and integration."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock OpenProject client."""
        client = OpenProjectClient()
        client._make_request = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_hal_json_parsing(self, mock_client):
        """Test that HAL+JSON responses are parsed correctly."""
        # Mock HAL+JSON response
        mock_response = {
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "name": "Test Project",
                        "_links": {
                            "self": {"href": "/api/v3/projects/1"}
                        }
                    }
                ]
            },
            "total": 1,
            "_links": {
                "self": {"href": "/api/v3/projects"}
            }
        }
        
        mock_client._make_request.return_value = mock_response
        
        # Test projects endpoint
        projects = await mock_client.get_projects()
        
        assert len(projects) == 1
        assert projects[0]["id"] == 1
        assert projects[0]["name"] == "Test Project"
        mock_client._make_request.assert_called_once_with("GET", "/projects")

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_client):
        """Test OpenProject-specific error response handling."""
        # Mock error response with HAL+JSON structure
        error_data = {
            "_embedded": {
                "errors": [
                    {
                        "message": "Name can't be blank",
                        "_links": {
                            "self": {"href": "/api/v3/errors/validation"}
                        }
                    }
                ]
            },
            "errors": {
                "name": ["can't be blank"]
            }
        }
        
        mock_client._make_request.side_effect = OpenProjectAPIError(
            "Validation failed", 
            status_code=422, 
            response_data=error_data
        )
        
        with pytest.raises(OpenProjectAPIError) as exc_info:
            await mock_client.get_projects()
        
        assert "Name can't be blank" in str(exc_info.value)
        assert hasattr(exc_info.value, 'detailed_errors')
        assert hasattr(exc_info.value, 'validation_errors')

    @pytest.mark.asyncio
    async def test_pagination(self, mock_client):
        """Test pagination handling for large result sets."""
        # Mock paginated responses
        page1_response = {
            "_embedded": {
                "elements": [{"id": i, "name": f"Project {i}"} for i in range(1, 101)]
            },
            "total": 150,
            "pageSize": 100,
            "offset": 0
        }
        
        page2_response = {
            "_embedded": {
                "elements": [{"id": i, "name": f"Project {i}"} for i in range(101, 151)]
            },
            "total": 150,
            "pageSize": 100,
            "offset": 100
        }
        
        mock_client._make_request.side_effect = [page1_response, page2_response]
        
        # Test paginated results
        all_projects = await mock_client.get_paginated_results("/projects")
        
        assert len(all_projects) == 150
        assert all_projects[0]["id"] == 1
        assert all_projects[-1]["id"] == 150
        assert mock_client._make_request.call_count == 2

    @pytest.mark.asyncio
    async def test_user_management(self, mock_client):
        """Test user management endpoints."""
        # Test get_users
        mock_users_response = {
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "login": "john.doe"
                    }
                ]
            }
        }
        mock_client._make_request.return_value = mock_users_response
        
        users = await mock_client.get_users()
        assert len(users) == 1
        assert users[0]["name"] == "John Doe"
        
        # Test get_user_by_email
        user = await mock_client.get_user_by_email("john@example.com")
        assert user["email"] == "john@example.com"
        
        # Test get_user_by_id
        mock_client._make_request.return_value = users[0]
        user = await mock_client.get_user_by_id(1)
        assert user["id"] == 1

    @pytest.mark.asyncio
    async def test_caching_functionality(self, mock_client):
        """Test caching layer functionality."""
        # Mock response for cached data
        mock_types_response = {
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "Task"},
                    {"id": 2, "name": "Bug"}
                ]
            }
        }
        
        mock_client._fetch_work_package_types = AsyncMock(return_value=mock_types_response["_embedded"]["elements"])
        
        # First call should hit the API
        types1 = await mock_client.get_work_package_types(use_cache=True)
        assert mock_client._fetch_work_package_types.call_count == 1
        
        # Second call should use cache
        types2 = await mock_client.get_work_package_types(use_cache=True)
        assert mock_client._fetch_work_package_types.call_count == 1  # Not called again
        assert types1 == types2

    def test_validation_models(self):
        """Test Pydantic validation models."""
        # Test valid work package creation
        valid_wp = WorkPackageCreateRequest(
            subject="Test Work Package",
            project_id=1,
            start_date="2024-01-01",
            due_date="2024-01-31",
            estimated_hours=8.0
        )
        assert valid_wp.subject == "Test Work Package"
        assert valid_wp.estimated_hours == 8.0
        
        # Test invalid date format
        with pytest.raises(ValidationError) as exc_info:
            WorkPackageCreateRequest(
                subject="Test",
                project_id=1,
                start_date="01-01-2024"  # Invalid format
            )
        assert "Date must be in YYYY-MM-DD format" in str(exc_info.value)
        
        # Test due date before start date
        with pytest.raises(ValidationError) as exc_info:
            WorkPackageCreateRequest(
                subject="Test",
                project_id=1,
                start_date="2024-01-31",
                due_date="2024-01-01"  # Before start date
            )
        assert "Due date must be after start date" in str(exc_info.value)
        
        # Test negative estimated hours
        with pytest.raises(ValidationError) as exc_info:
            WorkPackageCreateRequest(
                subject="Test",
                project_id=1,
                estimated_hours=-5.0
            )
        assert "Estimated hours must be positive" in str(exc_info.value)

    def test_relation_validation(self):
        """Test work package relation validation."""
        # Test valid relation
        valid_relation = WorkPackageRelationCreateRequest(
            from_work_package_id=1,
            to_work_package_id=2,
            relation_type="follows",
            lag=2
        )
        assert valid_relation.from_work_package_id == 1
        assert valid_relation.to_work_package_id == 2
        
        # Test self-relation (invalid)
        with pytest.raises(ValidationError) as exc_info:
            WorkPackageRelationCreateRequest(
                from_work_package_id=1,
                to_work_package_id=1  # Same as from
            )
        assert "Work package cannot have a relation with itself" in str(exc_info.value)
        
        # Test invalid relation type
        with pytest.raises(ValidationError) as exc_info:
            WorkPackageRelationCreateRequest(
                from_work_package_id=1,
                to_work_package_id=2,
                relation_type="invalid_type"
            )
        assert "Invalid relation type" in str(exc_info.value)
        
        # Test negative lag
        with pytest.raises(ValidationError) as exc_info:
            WorkPackageRelationCreateRequest(
                from_work_package_id=1,
                to_work_package_id=2,
                lag=-1
            )
        assert "Lag must be zero or positive" in str(exc_info.value)
