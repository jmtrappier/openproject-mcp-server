#!/usr/bin/env python3
"""
Create Director of Technology Handover Project in OpenProject
Based on the handover brief requirements
"""
import asyncio
import os
import sys
import json
import base64
from datetime import datetime, timedelta
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENPROJECT_URL = os.getenv("OPENPROJECT_URL", "http://localhost:3000")
OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY", "")

class OpenProjectAPI:
    def __init__(self):
        self.base_url = OPENPROJECT_URL
        auth_string = base64.b64encode(f"apikey:{OPENPROJECT_API_KEY}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json"
        }
    
    async def test_connection(self):
        """Test API connection."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v3", headers=self.headers) as response:
                    return response.status == 200
        except:
            return False
    
    async def create_project(self, name, description=""):
        """Create a new project."""
        data = {
            "name": name,
            "description": {"raw": description}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v3/projects",
                headers=self.headers,
                json=data
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Project creation failed: {response.status} - {text}")
    
    async def create_work_package(self, project_id, subject, description="", start_date=None, due_date=None, parent_id=None):
        """Create a work package."""
        data = {
            "subject": subject,
            "description": {"raw": description},
            "_links": {
                "project": {"href": f"/api/v3/projects/{project_id}"},
                "type": {"href": "/api/v3/types/1"}  # Assuming Task type ID 1
            }
        }
        
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
        if parent_id:
            data["_links"]["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v3/work_packages",
                headers=self.headers,
                json=data
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Work package creation failed: {response.status} - {text}")
    
    async def create_relation(self, from_wp_id, to_wp_id, relation_type="follows"):
        """Create a dependency between work packages."""
        data = {
            "_links": {
                "from": {"href": f"/api/v3/work_packages/{from_wp_id}"},
                "to": {"href": f"/api/v3/work_packages/{to_wp_id}"}
            },
            "type": relation_type
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v3/relations",
                headers=self.headers,
                json=data
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    text = await response.text()
                    print(f"Warning: Relation creation failed: {response.status} - {text}")
                    return None

def calculate_dates():
    """Calculate project dates based on the handover brief."""
    # Project starts on 6 August 2025 (as specified in the brief)
    start_date = datetime(2025, 8, 6).date()
    
    # Week 1: 6-12 Aug 2025
    week1_start = start_date
    week1_end = start_date + timedelta(days=6)  # 7 working days
    
    # Week 2: 13-19 Aug 2025  
    week2_start = week1_end + timedelta(days=1)
    week2_end = week2_start + timedelta(days=6)
    
    # Week 3: 20-26 Aug 2025
    week3_start = week2_end + timedelta(days=1)
    week3_end = week3_start + timedelta(days=6)
    
    # Week 4: 27 Aug - 5 Sep 2025
    week4_start = week3_end + timedelta(days=1)
    week4_end = datetime(2025, 9, 5).date()  # End date specified in brief
    
    return {
        'week1': (week1_start, week1_end),
        'week2': (week2_start, week2_end),
        'week3': (week3_start, week3_end),
        'week4': (week4_start, week4_end)
    }

async def create_handover_project():
    """Create the complete handover project structure."""
    api = OpenProjectAPI()
    
    print("🔗 Testing OpenProject connection...")
    if not await api.test_connection():
        print("❌ Cannot connect to OpenProject. Check your configuration in .env")
        return False
    
    print("✅ Connected to OpenProject successfully!")
    
    # Create main project
    print("\n📁 Creating main project...")
    project = await api.create_project(
        "Director of Technology Handover",
        "Comprehensive 4-week handover project for Director of Technology departure (6 August - 5 September 2025)"
    )
    project_id = project["id"]
    print(f"✅ Project created: ID {project_id}")
    print(f"🌐 URL: {OPENPROJECT_URL}/projects/{project.get('identifier', project_id)}")
    
    # Calculate dates
    dates = calculate_dates()
    
    # Create weekly phase work packages
    print("\n📋 Creating weekly phases...")
    
    phase_wps = {}
    
    # Week 1 Phase
    week1_wp = await api.create_work_package(
        project_id,
        "Week 1 - Stakeholder Alignment & Critical Path",
        "Week 1 focus on stakeholder identification, succession planning, and critical project initiation",
        dates['week1'][0].strftime("%Y-%m-%d"),
        dates['week1'][1].strftime("%Y-%m-%d")
    )
    phase_wps['week1'] = week1_wp["id"]
    print(f"✅ Week 1 phase created: ID {week1_wp['id']}")
    
    # Week 2 Phase
    week2_wp = await api.create_work_package(
        project_id,
        "Week 2 - Technical Leadership Transition",
        "Week 2 focus on technical leadership role definitions and transition planning",
        dates['week2'][0].strftime("%Y-%m-%d"),
        dates['week2'][1].strftime("%Y-%m-%d")
    )
    phase_wps['week2'] = week2_wp["id"]
    print(f"✅ Week 2 phase created: ID {week2_wp['id']}")
    
    # Week 3 Phase
    week3_wp = await api.create_work_package(
        project_id,
        "Week 3 - Project & Client Handovers",
        "Week 3 focus on client relationship transfers and project-specific handovers",
        dates['week3'][0].strftime("%Y-%m-%d"),
        dates['week3'][1].strftime("%Y-%m-%d")
    )
    phase_wps['week3'] = week3_wp["id"]
    print(f"✅ Week 3 phase created: ID {week3_wp['id']}")
    
    # Week 4 Phase
    week4_wp = await api.create_work_package(
        project_id,
        "Week 4 - Process & Finalisation",
        "Week 4 focus on process documentation and final handover completion",
        dates['week4'][0].strftime("%Y-%m-%d"),
        dates['week4'][1].strftime("%Y-%m-%d")
    )
    phase_wps['week4'] = week4_wp["id"]
    print(f"✅ Week 4 phase created: ID {week4_wp['id']}")
    
    # Create detailed work packages
    print("\n📝 Creating detailed work packages...")
    
    created_wps = []
    
    # Week 1 Work Packages
    week1_tasks = [
        {
            "subject": "Stakeholder Meeting with Manager",
            "description": "Clarify handover stakeholders, priorities, and Lead→Manager transition timelines",
            "start_date": "2025-08-06",
            "due_date": "2025-08-06",
            "parent": phase_wps['week1']
        },
        {
            "subject": "Succession Plan Draft", 
            "description": "Create organisational succession plan framework for manager review",
            "start_date": "2025-08-07",
            "due_date": "2025-08-09",
            "parent": phase_wps['week1']
        },
        {
            "subject": "Director of Technology JD",
            "description": "Draft comprehensive job description for Director of Technology role",
            "start_date": "2025-08-08", 
            "due_date": "2025-08-10",
            "parent": phase_wps['week1']
        },
        {
            "subject": "Recs Engine Sales Handover Documentation - Start",
            "description": "Begin documenting pre-sale project status, client communications, and proposal details",
            "start_date": "2025-08-08",
            "due_date": "2025-08-12",
            "parent": phase_wps['week1']
        }
    ]
    
    # Week 2 Work Packages
    week2_tasks = [
        {
            "subject": "Lead FED Manager JD & Transition Plan",
            "description": "Create JD for Lead Frontend Developer Manager role and transition planning",
            "start_date": "2025-08-13",
            "due_date": "2025-08-15",
            "parent": phase_wps['week2']
        },
        {
            "subject": "Lead BED Manager JD & Transition Plan",
            "description": "Create JD for Lead Backend Developer Manager role and transition planning", 
            "start_date": "2025-08-13",
            "due_date": "2025-08-15",
            "parent": phase_wps['week2']
        },
        {
            "subject": "Lead QA Manager JD (New Role)",
            "description": "Define new Lead QA Manager position and responsibilities",
            "start_date": "2025-08-15",
            "due_date": "2025-08-18",
            "parent": phase_wps['week2']
        },
        {
            "subject": "Technology Team Resourcing Planning Model Handover",
            "description": "Document and transfer resourcing planning methodology and tools",
            "start_date": "2025-08-16",
            "due_date": "2025-08-18",
            "parent": phase_wps['week2']
        },
        {
            "subject": "Recs Engine Technical Documentation",
            "description": "Complete technical handover documentation for Recs Engine project",
            "start_date": "2025-08-15",
            "due_date": "2025-08-18",
            "parent": phase_wps['week2']
        }
    ]
    
    # Week 3 Work Packages  
    week3_tasks = [
        {
            "subject": "Complete Recs Engine Sales Handover",
            "description": "Finalise sales handover documentation and client relationship transfer",
            "start_date": "2025-08-20",
            "due_date": "2025-08-21",
            "parent": phase_wps['week3']
        },
        {
            "subject": "VWFS GitLab and Feature Flags Documentation",
            "description": "Document GitLab setup, processes, and feature flag management",
            "start_date": "2025-08-20",
            "due_date": "2025-08-22",
            "parent": phase_wps['week3']
        },
        {
            "subject": "VWFS Automation Testing Handover",
            "description": "Transfer automation testing processes and responsibilities",
            "start_date": "2025-08-22",
            "due_date": "2025-08-24",
            "parent": phase_wps['week3']
        },
        {
            "subject": "Storyblok Nandos Handover",
            "description": "Document Storyblok implementation and ongoing management for Nandos",
            "start_date": "2025-08-24",
            "due_date": "2025-08-25",
            "parent": phase_wps['week3']
        },
        {
            "subject": "VI Handover",
            "description": "Transfer VI project responsibilities (stakeholder TBC)",
            "start_date": "2025-08-23",
            "due_date": "2025-08-25",
            "parent": phase_wps['week3']
        }
    ]
    
    # Week 4 Work Packages
    week4_tasks = [
        {
            "subject": "SLA Handover Documentation",
            "description": "Document all project SLAs and transfer responsibility",
            "start_date": "2025-08-27",
            "due_date": "2025-08-29",
            "parent": phase_wps['week4']
        },
        {
            "subject": "Update Patch Management Policy",
            "description": "Review and update patch management policy documentation",
            "start_date": "2025-08-28",
            "due_date": "2025-08-30",
            "parent": phase_wps['week4']
        },
        {
            "subject": "Nandos SAM Documentation",
            "description": "Document Software Asset Management processes for Nandos",
            "start_date": "2025-08-30",
            "due_date": "2025-08-31",
            "parent": phase_wps['week4']
        },
        {
            "subject": "Team Handover - Performance Review Summaries",
            "description": "Compile and transfer team performance review summaries",
            "start_date": "2025-09-01",
            "due_date": "2025-09-03",
            "parent": phase_wps['week4']
        },
        {
            "subject": "R&D Write-ups Compilation",
            "description": "Compile all R&D project documentation and findings",
            "start_date": "2025-09-02",
            "due_date": "2025-09-04",
            "parent": phase_wps['week4']
        },
        {
            "subject": "QA Handover Processes",
            "description": "Document QA processes and transfer responsibilities",
            "start_date": "2025-09-03",
            "due_date": "2025-09-04",
            "parent": phase_wps['week4']
        },
        {
            "subject": "Final Handover Meetings",
            "description": "Conduct final stakeholder meetings and sign-offs",
            "start_date": "2025-09-04",
            "due_date": "2025-09-05",
            "parent": phase_wps['week4']
        }
    ]
    
    # Create all work packages
    all_tasks = week1_tasks + week2_tasks + week3_tasks + week4_tasks
    
    for i, task in enumerate(all_tasks, 1):
        try:
            wp = await api.create_work_package(
                project_id,
                task["subject"],
                task["description"],
                task["start_date"],
                task["due_date"],
                task["parent"]
            )
            created_wps.append({
                "id": wp["id"],
                "subject": task["subject"],
                "week": task.get("week", "unknown")
            })
            print(f"✅ [{i:2d}/{len(all_tasks)}] {task['subject'][:50]}...")
            
            # Small delay to avoid overwhelming the API
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Failed to create '{task['subject']}': {str(e)}")
    
    print(f"\n🎉 Project creation completed!")
    print(f"📊 Created {len(created_wps)} work packages")
    print(f"🌐 View Gantt chart: {OPENPROJECT_URL}/projects/{project.get('identifier', project_id)}/work_packages?view=gantt")
    print(f"📋 View project: {OPENPROJECT_URL}/projects/{project.get('identifier', project_id)}")
    
    return True

async def main():
    """Main execution function."""
    print("🚀 Director of Technology Handover Project Creator")
    print("=" * 60)
    
    if not OPENPROJECT_API_KEY or OPENPROJECT_API_KEY == "your_40_character_api_key_here":
        print("❌ Please configure your OpenProject API key in the .env file")
        print("   1. Edit .env file")
        print("   2. Set OPENPROJECT_URL to your OpenProject instance")
        print("   3. Set OPENPROJECT_API_KEY to your 40-character API key")
        return False
    
    try:
        success = await create_handover_project()
        if success:
            print("\n🎉 Handover project setup completed successfully!")
            print("\nNext steps:")
            print("1. Review the created project structure")
            print("2. Assign team members to work packages")
            print("3. Adjust dates if needed")
            print("4. Configure custom fields for handover tracking")
        return success
    except Exception as e:
        print(f"\n💥 Project creation failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Project creation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
