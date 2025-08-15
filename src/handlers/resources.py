"""MCP resource handlers for OpenProject data browsing."""
import json
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openproject_client import OpenProjectClient, OpenProjectAPIError
from config import settings


class ResourceHandler:
    """Handler for MCP resources."""
    
    def __init__(self, client: OpenProjectClient):
        self.client = client
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available MCP resources."""
        return [
            {
                "uri": "openproject://projects",
                "name": "OpenProject Projects",
                "description": "List of all projects in OpenProject",
                "mimeType": "application/json"
            },
            {
                "uri": "openproject://users",
                "name": "OpenProject Users", 
                "description": "List of all users in OpenProject",
                "mimeType": "application/json"
            }
        ]
    
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """Get resource data by URI."""
        try:
            if uri == "openproject://projects":
                return await self._get_projects_resource()
            elif uri == "openproject://users":
                return await self._get_users_resource()
            elif uri.startswith("openproject://project/"):
                project_id = int(uri.split("/")[-1])
                return await self._get_project_resource(project_id)
            elif uri.startswith("openproject://work-packages/"):
                project_id = int(uri.split("/")[-1])
                return await self._get_work_packages_resource(project_id)
            elif uri.startswith("openproject://work-package/"):
                wp_id = int(uri.split("/")[-1])
                return await self._get_work_package_resource(wp_id)
            elif uri.startswith("openproject://project-members/"):
                project_id = int(uri.split("/")[-1])
                return await self._get_project_members_resource(project_id)
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
                
        except Exception as e:
            return {
                "error": f"Failed to get resource: {str(e)}",
                "uri": uri
            }
    
    async def _get_projects_resource(self) -> Dict[str, Any]:
        """Get projects resource data."""
        try:
            projects = await self.client.get_projects()
            
            formatted_projects = []
            for project in projects:
                formatted_projects.append({
                    "id": project.get("id"),
                    "name": project.get("name"),
                    "description": project.get("description", {}).get("raw", ""),
                    "status": project.get("status"),
                    "identifier": project.get("identifier"),
                    "created_at": project.get("createdAt"),
                    "updated_at": project.get("updatedAt"),
                    "url": f"{settings.openproject_url}/projects/{project.get('identifier', project.get('id'))}"
                })
            
            return {
                "contents": [
                    {
                        "uri": "openproject://projects",
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "projects": formatted_projects,
                            "total": len(formatted_projects),
                            "retrieved_at": "now"
                        }, indent=2)
                    }
                ]
            }
            
        except OpenProjectAPIError as e:
            return {
                "error": f"OpenProject API error: {e.message}",
                "details": e.response_data
            }
    
    async def _get_users_resource(self) -> Dict[str, Any]:
        """Get users resource data."""
        try:
            # Note: This would require implementing get_users in the client
            # For now, return a placeholder
            return {
                "contents": [
                    {
                        "uri": "openproject://users",
                        "mimeType": "application/json", 
                        "text": json.dumps({
                            "message": "User listing not yet implemented",
                            "note": "This feature requires additional OpenProject API integration"
                        }, indent=2)
                    }
                ]
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get users: {str(e)}"
            }
    
    async def _get_project_resource(self, project_id: int) -> Dict[str, Any]:
        """Get specific project resource data."""
        try:
            projects = await self.client.get_projects()
            project = next((p for p in projects if p.get("id") == project_id), None)
            
            if not project:
                return {
                    "error": f"Project with ID {project_id} not found"
                }
            
            # Get work packages for this project
            work_packages = await self.client.get_work_packages(project_id)
            
            return {
                "contents": [
                    {
                        "uri": f"openproject://project/{project_id}",
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "project": {
                                "id": project.get("id"),
                                "name": project.get("name"),
                                "description": project.get("description", {}).get("raw", ""),
                                "status": project.get("status"),
                                "identifier": project.get("identifier"),
                                "created_at": project.get("createdAt"),
                                "updated_at": project.get("updatedAt"),
                                "url": f"{settings.openproject_url}/projects/{project.get('identifier', project.get('id'))}"
                            },
                            "work_packages_count": len(work_packages),
                            "retrieved_at": "now"
                        }, indent=2)
                    }
                ]
            }
            
        except OpenProjectAPIError as e:
            return {
                "error": f"OpenProject API error: {e.message}",
                "details": e.response_data
            }
    
    async def _get_work_packages_resource(self, project_id: int) -> Dict[str, Any]:
        """Get work packages resource data for a project."""
        try:
            work_packages = await self.client.get_work_packages(project_id)
            
            formatted_wps = []
            for wp in work_packages:
                formatted_wps.append({
                    "id": wp.get("id"),
                    "subject": wp.get("subject"),
                    "description": wp.get("description", {}).get("raw", ""),
                    "project_id": project_id,
                    "start_date": wp.get("startDate"),
                    "due_date": wp.get("dueDate"),
                    "status": wp.get("_links", {}).get("status", {}).get("title", "Unknown"),
                    "type": wp.get("_links", {}).get("type", {}).get("title", "Unknown"),
                    "priority": wp.get("_links", {}).get("priority", {}).get("title", "Unknown"),
                    "assignee": wp.get("_links", {}).get("assignee", {}).get("title", "Unassigned"),
                    "created_at": wp.get("createdAt"),
                    "updated_at": wp.get("updatedAt"),
                    "url": f"{settings.openproject_url}/work_packages/{wp.get('id')}"
                })
            
            return {
                "contents": [
                    {
                        "uri": f"openproject://work-packages/{project_id}",
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "work_packages": formatted_wps,
                            "project_id": project_id,
                            "total": len(formatted_wps),
                            "retrieved_at": "now"
                        }, indent=2)
                    }
                ]
            }
            
        except OpenProjectAPIError as e:
            return {
                "error": f"OpenProject API error: {e.message}",
                "details": e.response_data
            }
    
    async def _get_work_package_resource(self, wp_id: int) -> Dict[str, Any]:
        """Get specific work package resource data."""
        try:
            work_package = await self.client.get_work_package_by_id(wp_id)
            
            return {
                "contents": [
                    {
                        "uri": f"openproject://work-package/{wp_id}",
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "work_package": {
                                "id": work_package.get("id"),
                                "subject": work_package.get("subject"),
                                "description": work_package.get("description", {}).get("raw", ""),
                                "project": work_package.get("_links", {}).get("project", {}).get("title", "Unknown"),
                                "start_date": work_package.get("startDate"),
                                "due_date": work_package.get("dueDate"),
                                "status": work_package.get("_links", {}).get("status", {}).get("title", "Unknown"),
                                "type": work_package.get("_links", {}).get("type", {}).get("title", "Unknown"),
                                "priority": work_package.get("_links", {}).get("priority", {}).get("title", "Unknown"),
                                "assignee": work_package.get("_links", {}).get("assignee", {}).get("title", "Unassigned"),
                                "estimated_time": work_package.get("estimatedTime"),
                                "done_ratio": work_package.get("doneRatio", 0),
                                "created_at": work_package.get("createdAt"),
                                "updated_at": work_package.get("updatedAt"),
                                "url": f"{settings.openproject_url}/work_packages/{work_package.get('id')}"
                            },
                            "retrieved_at": "now"
                        }, indent=2)
                    }
                ]
            }
            
        except OpenProjectAPIError as e:
            return {
                "error": f"OpenProject API error: {e.message}",
                "details": e.response_data
            }
    
    async def _get_project_members_resource(self, project_id: int) -> Dict[str, Any]:
        """Get project members resource data."""
        try:
            # Note: This would require implementing get_project_members in the client
            # For now, return a placeholder
            return {
                "contents": [
                    {
                        "uri": f"openproject://project-members/{project_id}",
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "message": "Project members listing not yet implemented",
                            "project_id": project_id,
                            "note": "This feature requires additional OpenProject API integration"
                        }, indent=2)
                    }
                ]
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get project members: {str(e)}"
            }


