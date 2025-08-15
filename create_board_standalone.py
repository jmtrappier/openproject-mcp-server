#!/usr/bin/env python3
"""
Create handover board using direct OpenProject API calls
Based on the MCP server design but standalone
"""

import asyncio
import aiohttp
import base64
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenProjectDirectClient:
    def __init__(self):
        self.base_url = os.getenv("OPENPROJECT_URL", "http://localhost:8080")
        self.api_key = os.getenv("OPENPROJECT_API_KEY", "")
        
        auth_string = base64.b64encode(f'apikey:{self.api_key}'.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.session = None
        self.project_id = 6  # Director of Technology Handover

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, method, url, **kwargs):
        """Make HTTP request to OpenProject API"""
        full_url = f"{self.base_url}/api/v3{url}"
        
        try:
            async with self.session.request(method, full_url, **kwargs) as response:
                print(f"   Request: {method} {full_url}")
                print(f"   Status: {response.status}")
                
                if response.status in [200, 201, 204]:
                    text = await response.text()
                    print(f"   Response length: {len(text)} chars")
                    
                    if text.strip():
                        return json.loads(text)
                    return {}
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
        except Exception as e:
            raise Exception(f"Request error: {e}")

    async def test_connection(self):
        """Test API connection"""
        try:
            result = await self._make_request("GET", "")
            return {"success": True, "version": result.get("coreVersion", "Unknown")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_work_packages(self):
        """Get all work packages for the project"""
        try:
            print(f"   Making request to: /projects/{self.project_id}/work_packages?pageSize=200")
            result = await self._make_request("GET", f"/projects/{self.project_id}/work_packages?pageSize=200")
            print(f"   Raw result keys: {list(result.keys()) if result else 'None'}")
            
            elements = result.get('_embedded', {}).get('elements', [])
            total = result.get('total', 0)
            print(f"   API returned {len(elements)} of {total} work packages")
            
            if not elements and result:
                print(f"   Full result: {json.dumps(result, indent=2)[:500]}...")
            
            return elements
        except Exception as e:
            print(f"Error getting work packages: {e}")
            return []

    async def organize_work_packages(self, work_packages):
        """Organize work packages by their hierarchy for board display"""
        phases = []
        standalone_tasks = []
        
        for wp in work_packages:
            wp_id = wp.get('id')
            subject = wp.get('subject', '')
            
            # Get type and status
            type_data = wp.get('_embedded', {}).get('type', {})
            status_data = wp.get('_embedded', {}).get('status', {})
            type_name = type_data.get('name', 'Unknown')
            status_name = status_data.get('name', 'Unknown')
            
            # Check for parent relationship
            parent_link = wp.get('_links', {}).get('parent', {})
            parent_title = parent_link.get('title') if parent_link.get('href') else None
            
            if not parent_title and 'Week' in subject:  # Weekly phase
                phases.append({
                    'id': wp_id,
                    'subject': subject,
                    'type': type_name,
                    'status': status_name,
                    'tasks': []
                })
            elif parent_title:  # Task under a phase
                # Find parent phase and add task
                parent_found = False
                for phase in phases:
                    if phase['subject'] == parent_title:
                        phase['tasks'].append({
                            'id': wp_id,
                            'subject': subject,
                            'type': type_name,
                            'status': status_name,
                            'parent': parent_title
                        })
                        parent_found = True
                        break
                
                if not parent_found:
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

    async def create_board_structure(self):
        """Create and display the handover board structure"""
        print("🚀 Director of Technology Handover - Board Creator")
        print("Using OpenProject MCP Server Approach")
        print("=" * 70)
        
        # Test connection
        print("🔗 Testing OpenProject connection...")
        connection_test = await self.test_connection()
        
        if not connection_test.get('success', False):
            print("❌ Cannot connect to OpenProject")
            print(f"   Error: {connection_test.get('error', 'Unknown error')}")
            return False
        
        print("✅ Connected to OpenProject successfully!")
        print(f"   Version: {connection_test.get('version', 'Unknown')}")
        
        # Get work packages
        print(f"\n📦 Fetching work packages from project {self.project_id}...")
        work_packages = await self.get_work_packages()
        
        if not work_packages:
            print("❌ No work packages found")
            return False
        
        print(f"📋 Found {len(work_packages)} work packages")
        
        # Organize work packages
        print(f"\n🔄 Organizing work packages for board display...")
        organization = await self.organize_work_packages(work_packages)
        
        # Display structure
        await self.display_board_structure(organization)
        
        # Create board layout
        await self.create_kanban_layout(organization)
        
        # Provide manual instructions
        await self.provide_setup_instructions(organization)
        
        return True

    async def display_board_structure(self, organization):
        """Display the hierarchical structure"""
        print("\n🎯 Director of Technology Handover - Project Structure")
        print("=" * 80)
        
        # Display weekly phases with tasks
        for phase in organization['phases']:
            print(f"\n🗂️  {phase['type']}: {phase['subject']} (ID: {phase['id']})")
            print(f"   Status: {phase['status']}")
            
            if phase['tasks']:
                print(f"   📋 Tasks ({len(phase['tasks'])}):")
                for task in sorted(phase['tasks'], key=lambda x: x['id']):
                    print(f"      └── {task['subject']} (ID: {task['id']}) - {task['status']}")
            else:
                print("   ⚠️  No tasks found")
        
        # Display standalone tasks
        if organization['standalone_tasks']:
            print(f"\n📌 Standalone Tasks ({len(organization['standalone_tasks'])}):")
            for task in sorted(organization['standalone_tasks'], key=lambda x: x['id']):
                parent_info = f" - Parent: {task['parent']}" if task['parent'] else ""
                print(f"   • {task['subject']} (ID: {task['id']}) - {task['status']}{parent_info}")
        
        print(f"\n📊 Total Work Packages: {organization['total_count']}")

    async def create_kanban_layout(self, organization):
        """Create Kanban board layout simulation"""
        print(f"\n🏗️  Kanban Board Layout Simulation")
        print("=" * 60)
        
        # Define columns
        columns = {
            'To Do': [],
            'In Progress': [],
            'Review': [],
            'Done': []
        }
        
        # Collect all work packages
        all_wps = []
        
        # Add phases (these would be cards on the board)
        for phase in organization['phases']:
            all_wps.append({
                'id': phase['id'],
                'subject': phase['subject'],
                'status': phase['status'],
                'type': 'Phase',
                'is_phase': True
            })
            
            # Add tasks under each phase
            for task in phase['tasks']:
                all_wps.append({
                    'id': task['id'],
                    'subject': task['subject'],
                    'status': task['status'],
                    'type': 'Task',
                    'is_phase': False,
                    'parent': task['parent']
                })
        
        # Add standalone tasks
        for task in organization['standalone_tasks']:
            all_wps.append({
                'id': task['id'],
                'subject': task['subject'],
                'status': task['status'],
                'type': 'Task',
                'is_phase': False,
                'parent': task.get('parent')
            })
        
        # Distribute to columns based on status
        for wp in all_wps:
            status = wp['status'].lower()
            if 'progress' in status or 'active' in status:
                columns['In Progress'].append(wp)
            elif 'review' in status or 'resolved' in status:
                columns['Review'].append(wp)
            elif 'done' in status or 'closed' in status:
                columns['Done'].append(wp)
            else:
                columns['To Do'].append(wp)
        
        # Display columns
        for column_name, items in columns.items():
            print(f"\n📌 {column_name} ({len(items)} items)")
            print("-" * 40)
            
            if items:
                # Sort to show phases first
                sorted_items = sorted(items, key=lambda x: (not x.get('is_phase', False), x['id']))
                for item in sorted_items:
                    icon = "🗂️ " if item.get('is_phase', False) else "📝 "
                    indent = "" if item.get('is_phase', False) else "   "
                    truncated_subject = item['subject'][:50] + "..." if len(item['subject']) > 50 else item['subject']
                    print(f"{indent}{icon}{truncated_subject} (ID: {item['id']})")
            else:
                print("   (No items)")

    async def provide_setup_instructions(self, organization):
        """Provide detailed manual setup instructions"""
        print(f"\n💡 Manual Board Setup Instructions")
        print("=" * 60)
        
        print(f"🌐 OpenProject URL: {self.base_url}/projects/director-of-technology-handover")
        
        print(f"\n📋 Board Creation Steps:")
        print(f"1. Navigate to the project in OpenProject")
        print(f"2. Look for 'Boards' in the project navigation menu")
        print(f"3. If 'Boards' isn't visible:")
        print(f"   - Go to Project Settings → Modules")
        print(f"   - Enable the 'Boards' module")
        print(f"4. Click 'Create new board' or '+' button")
        print(f"5. Configure the board:")
        print(f"   - Name: 'Director of Technology Handover Board'")
        print(f"   - Description: 'Kanban board for 4-week handover process'")
        
        print(f"\n🏗️  Column Setup:")
        columns = ['To Do', 'In Progress', 'Review', 'Done']
        for i, col in enumerate(columns, 1):
            print(f"   {i}. Create column: '{col}'")
        
        print(f"\n📌 Adding Work Packages:")
        print(f"   - Total work packages to add: {organization['total_count']}")
        print(f"   - Use 'Add card' or '+' button in each column")
        print(f"   - Search by work package ID or subject name")
        
        print(f"\n🎯 Organization Tips:")
        print(f"   - Pin the 4 weekly phases at the top")
        print(f"   - Group tasks under their respective weekly phases")
        print(f"   - Use different colors for weeks:")
        print(f"     🔴 Week 1 (Foundation & Critical Path)")
        print(f"     🟡 Week 2 (Technical Documentation)")
        print(f"     🟠 Week 3 (Project & Client Handovers)")
        print(f"     🟢 Week 4 (Process & Finalisation)")
        
        print(f"\n📊 Work Package Summary:")
        for phase in organization['phases']:
            week_num = "Week " + phase['subject'].split('Week ')[1].split(' ')[0] if 'Week ' in phase['subject'] else "Phase"
            print(f"   {week_num}: {len(phase['tasks'])} tasks (Phase ID: {phase['id']})")
        
        if organization['standalone_tasks']:
            print(f"   Standalone: {len(organization['standalone_tasks'])} tasks")

    async def simulate_mcp_integration(self):
        """Show how this would work with MCP"""
        print(f"\n🛠️  MCP Server Integration")
        print("=" * 50)
        
        print(f"✅ This script demonstrates what the MCP server can do:")
        print(f"   📝 Fetch all work packages via get_work_packages tool")
        print(f"   🔄 Organize by hierarchy and status")
        print(f"   📊 Display structured board layout")
        print(f"   💡 Provide setup instructions")
        
        print(f"\n🎯 To integrate with Claude/MCP:")
        print(f"   1. Start the MCP server: python3 scripts/run_server.py")
        print(f"   2. Configure Claude Desktop with MCP server")
        print(f"   3. Ask Claude: 'Create a board for the handover project'")
        print(f"   4. Claude uses get_work_packages and provides instructions")

async def main():
    """Main function"""
    try:
        async with OpenProjectDirectClient() as client:
            success = await client.create_board_structure()
            
            if success:
                await client.simulate_mcp_integration()
                print(f"\n🎉 Board analysis completed successfully!")
                print(f"✅ All work packages organized and ready for board")
                print(f"✅ Manual setup instructions provided")
            
            return success
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
