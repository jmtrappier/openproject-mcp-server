#!/usr/bin/env python3
"""
Create handover board using OpenProject MCP Server components
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from openproject_client import OpenProjectClient, OpenProjectAPIError
from models import ProjectCreateRequest, WorkPackageCreateRequest


class HandoverBoardCreator:
    def __init__(self):
        self.client = OpenProjectClient()
        self.project_id = 6  # Director of Technology Handover project
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()

    async def get_all_work_packages(self):
        """Get all work packages for the handover project"""
        try:
            work_packages = await self.client.get_work_packages(self.project_id)
            print(f"📋 Found {len(work_packages)} work packages in the project")
            return work_packages
        except OpenProjectAPIError as e:
            print(f"❌ Error getting work packages: {e}")
            return []

    async def organize_work_packages(self, work_packages):
        """Organize work packages by their hierarchy"""
        phases = []
        tasks_by_phase = {}
        standalone_tasks = []
        
        for wp in work_packages:
            wp_id = wp.get('id')
            subject = wp.get('subject', '')
            
            # Get type and status from embedded data
            type_data = wp.get('_embedded', {}).get('type', {})
            status_data = wp.get('_embedded', {}).get('status', {})
            type_name = type_data.get('name', 'Unknown')
            status_name = status_data.get('name', 'Unknown')
            
            # Check for parent relationship
            parent_link = wp.get('_links', {}).get('parent', {})
            parent_title = parent_link.get('title') if parent_link.get('href') else None
            
            if not parent_title and 'Week' in subject:  # This is a weekly phase
                phases.append({
                    'id': wp_id,
                    'subject': subject,
                    'type': type_name,
                    'status': status_name,
                    'tasks': []
                })
            elif parent_title:  # This is a task under a phase
                # Find the parent phase
                parent_phase = None
                for phase in phases:
                    if phase['subject'] == parent_title:
                        parent_phase = phase
                        break
                
                if parent_phase:
                    parent_phase['tasks'].append({
                        'id': wp_id,
                        'subject': subject,
                        'type': type_name,
                        'status': status_name,
                        'parent': parent_title
                    })
                else:
                    standalone_tasks.append({
                        'id': wp_id,
                        'subject': subject,
                        'type': type_name,
                        'status': status_name,
                        'parent': parent_title
                    })
            else:  # Standalone task
                standalone_tasks.append({
                    'id': wp_id,
                    'subject': subject,
                    'type': type_name,
                    'status': status_name,
                    'parent': None
                })
        
        return {
            'phases': sorted(phases, key=lambda x: x['id']),
            'standalone_tasks': standalone_tasks,
            'total_count': len(work_packages)
        }

    async def display_board_structure(self, organization):
        """Display the current project structure"""
        print("\n🎯 Director of Technology Handover - Board Structure")
        print("=" * 80)
        
        # Display weekly phases with their tasks
        for phase in organization['phases']:
            print(f"\n🗂️  {phase['type']}: {phase['subject']} (ID: {phase['id']})")
            print(f"   Status: {phase['status']}")
            
            if phase['tasks']:
                print(f"   📋 Tasks ({len(phase['tasks'])}):")
                for task in sorted(phase['tasks'], key=lambda x: x['id']):
                    print(f"      └── {task['type']}: {task['subject']} (ID: {task['id']}) - {task['status']}")
            else:
                print("   ⚠️  No tasks found for this phase")
        
        # Display standalone tasks
        if organization['standalone_tasks']:
            print(f"\n📌 Standalone Tasks ({len(organization['standalone_tasks'])}):")
            for task in sorted(organization['standalone_tasks'], key=lambda x: x['id']):
                parent_info = f" - Parent: {task['parent']}" if task['parent'] else ""
                print(f"   • {task['type']}: {task['subject']} (ID: {task['id']}) - {task['status']}{parent_info}")
        
        print(f"\n📊 Total Work Packages: {organization['total_count']}")
        return organization

    async def simulate_board_creation(self, organization):
        """Simulate creating a Kanban board structure"""
        print(f"\n🏗️  Creating Kanban Board Structure...")
        
        # Define board columns based on status
        board_columns = {
            'To Do': [],
            'In Progress': [],
            'Review': [],
            'Done': []
        }
        
        # Organize all work packages by status
        all_work_packages = []
        
        # Add phases
        for phase in organization['phases']:
            all_work_packages.append({
                'id': phase['id'],
                'subject': phase['subject'],
                'type': phase['type'],
                'status': phase['status'],
                'is_phase': True
            })
            # Add phase tasks
            for task in phase['tasks']:
                all_work_packages.append({
                    'id': task['id'],
                    'subject': task['subject'],
                    'type': task['type'],
                    'status': task['status'],
                    'is_phase': False,
                    'parent': task['parent']
                })
        
        # Add standalone tasks
        for task in organization['standalone_tasks']:
            all_work_packages.append({
                'id': task['id'],
                'subject': task['subject'],
                'type': task['type'],
                'status': task['status'],
                'is_phase': False,
                'parent': task.get('parent')
            })
        
        # Distribute to columns based on status
        for wp in all_work_packages:
            status = wp['status'].lower()
            if 'progress' in status or 'active' in status:
                board_columns['In Progress'].append(wp)
            elif 'review' in status or 'resolved' in status:
                board_columns['Review'].append(wp)
            elif 'done' in status or 'closed' in status:
                board_columns['Done'].append(wp)
            else:
                board_columns['To Do'].append(wp)
        
        # Display board structure
        print("\n📋 Kanban Board Layout:")
        print("=" * 80)
        
        for column_name, work_packages in board_columns.items():
            print(f"\n📌 {column_name} ({len(work_packages)} items)")
            print("-" * 40)
            
            if work_packages:
                for wp in sorted(work_packages, key=lambda x: (not x.get('is_phase', False), x['id'])):
                    icon = "🗂️ " if wp.get('is_phase', False) else "📝 "
                    indent = "" if wp.get('is_phase', False) else "   "
                    print(f"{indent}{icon}{wp['subject']} (ID: {wp['id']})")
            else:
                print("   (No items)")
        
        return board_columns

    async def provide_manual_instructions(self, organization):
        """Provide instructions for manual board setup"""
        print(f"\n💡 Manual Board Setup Instructions:")
        print("=" * 60)
        
        print(f"1. 🌐 Navigate to: http://localhost:8080/projects/director-of-technology-handover")
        print(f"2. 📋 Look for 'Boards' in the project menu")
        print(f"3. ➕ Click 'Create new board' or '+' button")
        print(f"4. 📝 Configure board:")
        print(f"   - Name: 'Director of Technology Handover Board'")
        print(f"   - Description: 'Kanban board for 4-week handover process'")
        
        print(f"\n5. 🏗️  Create columns:")
        columns = ['To Do', 'In Progress', 'Review', 'Done']
        for i, col in enumerate(columns, 1):
            print(f"   {i}. {col}")
        
        print(f"\n6. 📌 Add work packages to board:")
        print(f"   - Use 'Add card' or '+' button in each column")
        print(f"   - Search by ID or subject name")
        print(f"   - Total: {organization['total_count']} work packages to add")
        
        print(f"\n7. 🎯 Recommended organization:")
        print(f"   - Pin weekly phases at top of columns")
        print(f"   - Group tasks under their weekly phases")
        print(f"   - Use colors to distinguish weeks:")
        print(f"     🔴 Week 1 (High Priority)")
        print(f"     🟡 Week 2-3 (Medium Priority)")
        print(f"     🟢 Week 4 (Buffer/Final)")

    async def test_mcp_tools_simulation(self):
        """Simulate using MCP tools for board creation"""
        print(f"\n🛠️  MCP Tools Simulation:")
        print("=" * 50)
        
        print("✅ Available MCP Tools:")
        tools = [
            "create_project",
            "create_work_package", 
            "create_work_package_dependency",
            "get_projects",
            "get_work_packages",
            "update_work_package",
            "get_project_summary"
        ]
        
        for tool in tools:
            print(f"   📝 {tool}")
        
        print(f"\n✅ Available MCP Resources:")
        resources = [
            "openproject://projects",
            "openproject://project/6",
            "openproject://work-packages/6",
            "openproject://work-package/{id}"
        ]
        
        for resource in resources:
            print(f"   🔗 {resource}")
        
        print(f"\n🎯 Board creation approach:")
        print(f"   1. ✅ Use get_work_packages(6) to fetch all tasks")
        print(f"   2. ✅ Organize by hierarchy and status") 
        print(f"   3. ⚠️  Board creation API not available in OpenProject")
        print(f"   4. 💡 Manual board setup required via web interface")

async def main():
    """Main function to create the handover board"""
    print("🚀 Director of Technology Handover - Board Creator")
    print("Using OpenProject MCP Server Components")
    print("=" * 70)
    
    try:
        async with HandoverBoardCreator() as creator:
            # Test connection first
            print("🔗 Testing OpenProject connection...")
            connection_test = await creator.client.test_connection()
            
            if not connection_test.get('success', False):
                print("❌ Cannot connect to OpenProject")
                print("   Check your .env configuration")
                return False
            
            print("✅ Connected to OpenProject successfully!")
            print(f"   Version: {connection_test.get('version', 'Unknown')}")
            
            # Get all work packages
            print(f"\n📦 Fetching work packages from project {creator.project_id}...")
            work_packages = await creator.get_all_work_packages()
            
            if not work_packages:
                print("❌ No work packages found. Please run the project creation script first.")
                return False
            
            # Organize work packages
            print(f"\n🔄 Organizing work packages...")
            organization = await creator.organize_work_packages(work_packages)
            
            # Display current structure
            await creator.display_board_structure(organization)
            
            # Simulate board creation
            board_columns = await creator.simulate_board_creation(organization)
            
            # Provide manual instructions
            await creator.provide_manual_instructions(organization)
            
            # Show MCP tools simulation
            await creator.test_mcp_tools_simulation()
            
            print(f"\n🎉 Board setup analysis completed!")
            print(f"✅ {organization['total_count']} work packages ready for board")
            print(f"✅ {len(organization['phases'])} weekly phases identified")
            print(f"✅ Manual setup instructions provided")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)



