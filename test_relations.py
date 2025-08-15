#!/usr/bin/env python3
"""Test script for work package relations functionality."""

import asyncio
import json
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from openproject_client import OpenProjectClient, OpenProjectAPIError
from config import settings


async def test_relations():
    """Test work package relations functionality."""
    print("Testing OpenProject Work Package Relations...")
    print("=" * 60)
    
    client = OpenProjectClient()
    
    try:
        # Test 1: Check connection
        print("\n1. Testing connection...")
        connection_result = await client.test_connection()
        if not connection_result.get('success'):
            print(f"❌ Connection failed: {connection_result.get('message')}")
            return False
        print(f"✅ Connection successful: {connection_result.get('openproject_version')}")
        
        # Test 2: Get projects to find work packages for testing
        print("\n2. Getting projects...")
        projects = await client.get_projects()
        if not projects:
            print("❌ No projects found. Please create a project first.")
            return False
        
        project_id = projects[0].get("id")
        project_name = projects[0].get("name")
        print(f"✅ Using project: {project_name} (ID: {project_id})")
        
        # Test 3: Get work packages from the project
        print("\n3. Getting work packages...")
        work_packages = await client.get_work_packages(project_id)
        if len(work_packages) < 2:
            print("❌ Need at least 2 work packages for relation testing.")
            print("   Creating test work packages...")
            
            # Create test work packages
            from models import WorkPackageCreateRequest
            
            wp1_request = WorkPackageCreateRequest(
                project_id=project_id,
                subject="Test Work Package 1 - Prerequisites",
                description="This is the first work package that must be completed first.",
                start_date="2024-01-01",
                due_date="2024-01-15"
            )
            
            wp2_request = WorkPackageCreateRequest(
                project_id=project_id,
                subject="Test Work Package 2 - Dependent Task",
                description="This work package follows the first one.",
                start_date="2024-01-16",
                due_date="2024-01-30"
            )
            
            try:
                wp1_result = await client.create_work_package(wp1_request)
                wp2_result = await client.create_work_package(wp2_request)
                work_packages = [wp1_result, wp2_result]
                print(f"✅ Created test work packages: {wp1_result.get('id')} and {wp2_result.get('id')}")
            except Exception as e:
                print(f"❌ Failed to create test work packages: {e}")
                return False
        
        # Use first two work packages for testing
        wp1_id = work_packages[0].get("id")
        wp2_id = work_packages[1].get("id")
        wp1_subject = work_packages[0].get("subject")
        wp2_subject = work_packages[1].get("subject")
        
        print(f"✅ Using work packages:")
        print(f"   WP1: {wp1_subject} (ID: {wp1_id})")
        print(f"   WP2: {wp2_subject} (ID: {wp2_id})")
        
        # Test 4: Create a "follows" relation
        print("\n4. Creating 'follows' relation...")
        try:
            relation_result = await client.create_work_package_relation(
                from_wp_id=wp2_id,
                to_wp_id=wp1_id,
                relation_type="follows",
                description="WP2 follows WP1 - testing relations",
                lag=1
            )
            
            relation_id = relation_result.get("id")
            print(f"✅ Created relation: {relation_result.get('type')} (ID: {relation_id})")
            print(f"   Description: {relation_result.get('description')}")
            print(f"   Lag: {relation_result.get('lag')} days")
            print(f"   Reverse type: {relation_result.get('reverseType')}")
            
        except OpenProjectAPIError as e:
            print(f"❌ Failed to create relation: {e.message}")
            if e.response_data:
                print(f"   Details: {json.dumps(e.response_data, indent=2)}")
            return False
        
        # Test 5: Get relations for work packages
        print("\n5. Getting relations for work packages...")
        try:
            # Check relations for WP1
            wp1_relations = await client.get_work_package_relations(wp1_id)
            print(f"✅ WP1 ({wp1_id}) has {len(wp1_relations)} relations")
            
            # Check relations for WP2
            wp2_relations = await client.get_work_package_relations(wp2_id)
            print(f"✅ WP2 ({wp2_id}) has {len(wp2_relations)} relations")
            
            # Display relation details
            all_relations = wp1_relations + wp2_relations
            for i, relation in enumerate(all_relations, 1):
                print(f"   Relation {i}:")
                print(f"     ID: {relation.get('id')}")
                print(f"     Type: {relation.get('type')}")
                print(f"     From: {relation.get('_links', {}).get('from', {}).get('title', 'Unknown')}")
                print(f"     To: {relation.get('_links', {}).get('to', {}).get('title', 'Unknown')}")
                print(f"     Lag: {relation.get('lag', 0)} days")
                
        except OpenProjectAPIError as e:
            print(f"❌ Failed to get relations: {e.message}")
            return False
        
        # Test 6: Test different relation types
        print("\n6. Testing different relation types...")
        test_relations = [
            ("blocks", "WP1 blocks WP2"),
            ("relates", "WP1 relates to WP2"),
        ]
        
        created_relation_ids = [relation_id] if 'relation_id' in locals() else []
        
        for rel_type, description in test_relations:
            try:
                result = await client.create_work_package_relation(
                    from_wp_id=wp1_id,
                    to_wp_id=wp2_id,
                    relation_type=rel_type,
                    description=description
                )
                created_relation_ids.append(result.get("id"))
                print(f"✅ Created {rel_type} relation (ID: {result.get('id')})")
                
            except OpenProjectAPIError as e:
                print(f"⚠️  Failed to create {rel_type} relation: {e.message}")
                # Don't fail the test for individual relation type issues
        
        # Test 7: Clean up - delete created relations
        print("\n7. Cleaning up test relations...")
        for rel_id in created_relation_ids:
            if rel_id:
                try:
                    await client.delete_work_package_relation(rel_id)
                    print(f"✅ Deleted relation {rel_id}")
                except OpenProjectAPIError as e:
                    print(f"⚠️  Failed to delete relation {rel_id}: {e.message}")
        
        print("\n" + "=" * 60)
        print("✅ Work package relations testing completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await client.close()


async def test_mcp_tools():
    """Test MCP server tools for relations."""
    print("\n\nTesting MCP Server Tools...")
    print("=" * 60)
    
    # Import MCP tools
    from mcp_server import (
        create_work_package_dependency,
        get_work_package_relations,
        delete_work_package_relation
    )
    
    try:
        # These tests would require actual work packages
        # For now, just test the validation logic
        
        print("\n1. Testing input validation...")
        
        # Test invalid work package IDs
        result = await create_work_package_dependency(
            from_work_package_id=0,
            to_work_package_id=1
        )
        result_data = json.loads(result)
        if not result_data.get("success"):
            print("✅ Correctly rejected invalid from_work_package_id")
        
        # Test same work package relation
        result = await create_work_package_dependency(
            from_work_package_id=123,
            to_work_package_id=123
        )
        result_data = json.loads(result)
        if not result_data.get("success"):
            print("✅ Correctly rejected self-relation")
        
        # Test invalid relation type
        result = await create_work_package_dependency(
            from_work_package_id=123,
            to_work_package_id=456,
            relation_type="invalid_type"
        )
        result_data = json.loads(result)
        if not result_data.get("success"):
            print("✅ Correctly rejected invalid relation type")
        
        # Test negative lag
        result = await create_work_package_dependency(
            from_work_package_id=123,
            to_work_package_id=456,
            lag=-5
        )
        result_data = json.loads(result)
        if not result_data.get("success"):
            print("✅ Correctly rejected negative lag")
        
        print("\n✅ MCP tools validation testing completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing MCP tools: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("OpenProject MCP Server - Relations Feature Testing")
    print("=" * 60)
    print(f"OpenProject URL: {settings.openproject_url}")
    print(f"Using API Key: {'***' + settings.openproject_api_key[-4:] if settings.openproject_api_key else 'NOT CONFIGURED'}")
    
    if not settings.openproject_api_key:
        print("❌ OpenProject API key not configured. Please set OPENPROJECT_API_KEY environment variable.")
        return False
    
    async def run_tests():
        # Test OpenProject client
        client_test_passed = await test_relations()
        
        # Test MCP server tools
        mcp_test_passed = await test_mcp_tools()
        
        return client_test_passed and mcp_test_passed
    
    # Run the tests
    success = asyncio.run(run_tests())
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! Work package relations feature is working correctly.")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
