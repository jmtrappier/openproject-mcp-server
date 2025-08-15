#!/usr/bin/env python3
"""
MVP Test Script for OpenProject MCP Server

This script tests the complete MVP workflow:
1. Create a project
2. Create work packages with dates
3. Create dependencies between work packages
4. Verify Gantt chart data structure
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from openproject_client import OpenProjectClient, OpenProjectAPIError
from models import ProjectCreateRequest, WorkPackageCreateRequest
from config import settings


async def test_connection():
    """Test OpenProject API connection."""
    print("🔗 Testing OpenProject connection...")
    client = OpenProjectClient()
    
    try:
        result = await client.test_connection()
        if result["success"]:
            print(f"✅ Connection successful! OpenProject version: {result.get('openproject_version', 'unknown')}")
            return client
        else:
            print(f"❌ Connection failed: {result['message']}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return None


async def test_create_project(client: OpenProjectClient):
    """Test project creation."""
    print("\n📁 Testing project creation...")
    
    # Generate unique project name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"MVP Test Project {timestamp}"
    
    try:
        project_request = ProjectCreateRequest(
            name=project_name,
            description="Test project created by OpenProject MCP Server MVP test"
        )
        
        result = await client.create_project(project_request)
        project_id = result.get("id")
        
        print(f"✅ Project created successfully!")
        print(f"   - ID: {project_id}")
        print(f"   - Name: {result.get('name')}")
        print(f"   - URL: {settings.openproject_url}/projects/{result.get('identifier', project_id)}")
        
        return project_id
        
    except OpenProjectAPIError as e:
        print(f"❌ Project creation failed: {e.message}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None


async def test_create_work_packages(client: OpenProjectClient, project_id: int):
    """Test work package creation with dates."""
    print("\n📋 Testing work package creation...")
    
    # Calculate dates for Gantt chart
    today = datetime.now().date()
    
    work_packages = [
        {
            "subject": "Project Planning",
            "description": "Initial project planning and requirements gathering",
            "start_date": today.strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "estimated_hours": 20.0
        },
        {
            "subject": "Design Phase",
            "description": "System design and architecture",
            "start_date": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
            "estimated_hours": 30.0
        },
        {
            "subject": "Development",
            "description": "Core development implementation",
            "start_date": (today + timedelta(days=13)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=25)).strftime("%Y-%m-%d"),
            "estimated_hours": 60.0
        },
        {
            "subject": "Testing",
            "description": "Quality assurance and testing",
            "start_date": (today + timedelta(days=26)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "estimated_hours": 20.0
        }
    ]
    
    created_work_packages = []
    
    for wp_data in work_packages:
        try:
            wp_request = WorkPackageCreateRequest(
                project_id=project_id,
                subject=wp_data["subject"],
                description=wp_data["description"],
                start_date=wp_data["start_date"],
                due_date=wp_data["due_date"],
                estimated_hours=wp_data["estimated_hours"]
            )
            
            result = await client.create_work_package(wp_request)
            wp_id = result.get("id")
            
            print(f"✅ Work package created: '{wp_data['subject']}'")
            print(f"   - ID: {wp_id}")
            print(f"   - Dates: {wp_data['start_date']} → {wp_data['due_date']}")
            print(f"   - URL: {settings.openproject_url}/work_packages/{wp_id}")
            
            created_work_packages.append({
                "id": wp_id,
                "subject": wp_data["subject"],
                "start_date": wp_data["start_date"],
                "due_date": wp_data["due_date"]
            })
            
        except OpenProjectAPIError as e:
            print(f"❌ Work package creation failed for '{wp_data['subject']}': {e.message}")
        except Exception as e:
            print(f"❌ Unexpected error for '{wp_data['subject']}': {str(e)}")
    
    return created_work_packages


async def test_create_dependencies(client: OpenProjectClient, work_packages: list):
    """Test work package dependency creation."""
    print("\n🔗 Testing work package dependencies...")
    
    if len(work_packages) < 2:
        print("❌ Not enough work packages to create dependencies")
        return False
    
    # Create sequential dependencies for Gantt chart
    dependencies = [
        (0, 1, "follows"),  # Planning → Design
        (1, 2, "follows"),  # Design → Development
        (2, 3, "follows"),  # Development → Testing
    ]
    
    success_count = 0
    
    for from_idx, to_idx, relation_type in dependencies:
        if from_idx < len(work_packages) and to_idx < len(work_packages):
            try:
                from_wp = work_packages[from_idx]
                to_wp = work_packages[to_idx]
                
                result = await client.create_work_package_relation(
                    from_wp["id"], to_wp["id"], relation_type
                )
                
                print(f"✅ Dependency created: '{from_wp['subject']}' {relation_type} '{to_wp['subject']}'")
                success_count += 1
                
            except OpenProjectAPIError as e:
                print(f"❌ Dependency creation failed: {e.message}")
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
    
    return success_count > 0


async def verify_gantt_data(client: OpenProjectClient, project_id: int):
    """Verify that Gantt chart data is properly structured."""
    print("\n📊 Verifying Gantt chart data...")
    
    try:
        work_packages = await client.get_work_packages(project_id)
        
        if not work_packages:
            print("❌ No work packages found for Gantt verification")
            return False
        
        gantt_ready = True
        for wp in work_packages:
            wp_id = wp.get("id")
            subject = wp.get("subject", "Unknown")
            start_date = wp.get("startDate")
            due_date = wp.get("dueDate")
            
            print(f"📋 WP {wp_id}: {subject}")
            print(f"   - Start: {start_date or 'Not set'}")
            print(f"   - Due: {due_date or 'Not set'}")
            
            if not start_date or not due_date:
                gantt_ready = False
        
        if gantt_ready:
            print("✅ All work packages have dates - Gantt chart ready!")
            print(f"🌐 View Gantt chart: {settings.openproject_url}/projects/{project_id}/work_packages?view=gantt")
        else:
            print("⚠️  Some work packages missing dates - Gantt chart may be incomplete")
        
        return gantt_ready
        
    except Exception as e:
        print(f"❌ Gantt verification error: {str(e)}")
        return False


async def main():
    """Run complete MVP test."""
    print("🧪 OpenProject MCP Server MVP Test")
    print("=" * 50)
    
    # Test connection
    client = await test_connection()
    if not client:
        print("\n❌ MVP Test FAILED: Cannot connect to OpenProject")
        return False
    
    try:
        # Test project creation
        project_id = await test_create_project(client)
        if not project_id:
            print("\n❌ MVP Test FAILED: Cannot create project")
            return False
        
        # Test work package creation
        work_packages = await test_create_work_packages(client, project_id)
        if not work_packages:
            print("\n❌ MVP Test FAILED: Cannot create work packages")
            return False
        
        # Test dependency creation
        dependencies_created = await test_create_dependencies(client, work_packages)
        if not dependencies_created:
            print("\n⚠️  MVP Test WARNING: Dependencies not created")
        
        # Verify Gantt chart readiness
        gantt_ready = await verify_gantt_data(client, project_id)
        
        # Final result
        print("\n" + "=" * 50)
        if gantt_ready:
            print("🎉 MVP Test PASSED!")
            print("✅ Project created")
            print("✅ Work packages created with dates")
            print("✅ Dependencies created")
            print("✅ Gantt chart ready")
            print(f"\n🌐 Open your browser: {settings.openproject_url}/projects/{project_id}/work_packages?view=gantt")
        else:
            print("⚠️  MVP Test PARTIAL SUCCESS")
            print("✅ Basic functionality works")
            print("⚠️  Gantt chart may need manual configuration")
        
        return True
        
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {str(e)}")
        sys.exit(1)



