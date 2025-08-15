#!/usr/bin/env python3
"""
Add "Offboarding of machine and accounts" task to the handover project
"""

import asyncio
import aiohttp
import base64
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenProjectTaskAdder:
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
                if response.status in [200, 201, 204]:
                    text = await response.text()
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

    async def create_offboarding_task(self):
        """Create the offboarding task as the final task in the handover project"""
        
        # Task details
        task_data = {
            "subject": "Offboarding of machine and accounts",
            "description": {
                "raw": "Complete offboarding process including:\n- Return company equipment (laptop, mobile, etc.)\n- Deactivate all system accounts and access\n- Remove from security groups and email lists\n- Complete final IT checklist\n- Handover any remaining access credentials"
            },
            "startDate": "2025-09-05",  # Start on final day
            "dueDate": "2025-09-05",    # Complete on final day
            "_links": {
                "project": {"href": f"/api/v3/projects/{self.project_id}"},
                "type": {"href": "/api/v3/types/1"}  # Task type
            }
        }
        
        try:
            result = await self._make_request("POST", "/work_packages", json=task_data)
            return result
        except Exception as e:
            raise Exception(f"Failed to create offboarding task: {e}")

    async def get_current_work_packages(self):
        """Get current work packages to show the addition"""
        try:
            result = await self._make_request("GET", f"/projects/{self.project_id}/work_packages?pageSize=50")
            return result.get('_embedded', {}).get('elements', [])
        except Exception as e:
            print(f"Error getting work packages: {e}")
            return []

    async def add_offboarding_task(self):
        """Main function to add the offboarding task"""
        print("🚀 Adding Offboarding Task to Handover Project")
        print("=" * 60)
        
        # Test connection
        print("🔗 Testing OpenProject connection...")
        connection_test = await self.test_connection()
        
        if not connection_test.get('success', False):
            print("❌ Cannot connect to OpenProject")
            print(f"   Error: {connection_test.get('error', 'Unknown error')}")
            return False
        
        print("✅ Connected to OpenProject successfully!")
        print(f"   Version: {connection_test.get('version', 'Unknown')}")
        
        # Get current work packages count
        print(f"\n📊 Checking current project status...")
        current_wps = await self.get_current_work_packages()
        print(f"   Current work packages: {len(current_wps)}")
        
        # Create the offboarding task
        print(f"\n📝 Creating offboarding task...")
        try:
            new_task = await self.create_offboarding_task()
            task_id = new_task.get('id')
            task_subject = new_task.get('subject')
            
            print(f"✅ Successfully created offboarding task!")
            print(f"   ID: {task_id}")
            print(f"   Subject: {task_subject}")
            print(f"   Date: September 5, 2025 (Final day)")
            print(f"   URL: {self.base_url}/work_packages/{task_id}")
            
            # Show updated count
            updated_wps = await self.get_current_work_packages()
            print(f"\n📊 Updated project status:")
            print(f"   Total work packages: {len(updated_wps)} (+1)")
            
            print(f"\n🎯 Task Details:")
            print(f"   Purpose: Complete final offboarding process")
            print(f"   Includes: Equipment return, account deactivation, access removal")
            print(f"   Timeline: Final day of handover (September 5, 2025)")
            print(f"   Type: Standalone task (not part of weekly phases)")
            
            print(f"\n📋 Updated Handover Structure:")
            print(f"   • 4 Weekly Phases (108-111)")
            print(f"   • 26 Individual Tasks (nested under phases)")
            print(f"   • 1 Team Catch-ups Task (138)")
            print(f"   • 1 Offboarding Task ({task_id}) ← NEW")
            print(f"   • Total: {len(updated_wps)} work packages")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create offboarding task: {e}")
            return False

async def main():
    """Main function"""
    try:
        async with OpenProjectTaskAdder() as adder:
            success = await adder.add_offboarding_task()
            
            if success:
                print(f"\n🎉 Offboarding task added successfully!")
                print(f"✅ Your handover project now includes the final offboarding step")
                print(f"✅ Timeline complete from August 7 - September 5, 2025")
                print(f"✅ Ready for board update (if you're using one)")
            
            return success
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)



