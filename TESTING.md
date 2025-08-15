# OpenProject MCP Server - Testing Instructions

## 🧪 MVP Testing Guide

This document provides comprehensive testing instructions for the OpenProject MCP Server MVP implementation.

## Prerequisites

Before testing, ensure you have:

1. **OpenProject instance** running and accessible
2. **API key** generated from your OpenProject user profile
3. **Python 3.8+** installed
4. **Virtual environment** activated
5. **Dependencies** installed from `requirements.txt`

## Environment Setup

1. **Copy environment file**:
   ```bash
   cp env.example .env
   ```

2. **Configure environment variables**:
   ```env
   OPENPROJECT_URL=http://localhost:3000
   OPENPROJECT_API_KEY=your_40_character_api_key_here
   ```

3. **Verify configuration**:
   ```bash
   python3 -c "from src.config import settings; print(f'URL: {settings.openproject_url}')"
   ```

## Testing Methods

### Method 1: Automated MVP Test (Recommended)

Run the comprehensive MVP test script:

```bash
python3 scripts/test_mvp.py
```

**What it tests:**
- ✅ OpenProject API connection
- ✅ Project creation functionality  
- ✅ Work package creation with dates
- ✅ Dependency creation between work packages
- ✅ Gantt chart data structure verification

**Expected output:**
```
🧪 OpenProject MCP Server MVP Test
==================================================
🔗 Testing OpenProject connection...
✅ Connection successful! OpenProject version: 13.0.0

📁 Testing project creation...
✅ Project created successfully!
   - ID: 123
   - Name: MVP Test Project 20241220_143022
   - URL: http://localhost:3000/projects/123

📋 Testing work package creation...
✅ Work package created: 'Project Planning'
   - ID: 456
   - Dates: 2024-12-20 → 2024-12-25
   - URL: http://localhost:3000/work_packages/456
... (more work packages)

🔗 Testing work package dependencies...
✅ Dependency created: 'Project Planning' follows 'Design Phase'
... (more dependencies)

📊 Verifying Gantt chart data...
✅ All work packages have dates - Gantt chart ready!
🌐 View Gantt chart: http://localhost:3000/projects/123/work_packages?view=gantt

==================================================
🎉 MVP Test PASSED!
✅ Project created
✅ Work packages created with dates  
✅ Dependencies created
✅ Gantt chart ready
```

### Method 2: Manual Testing

#### Test 1: Connection Verification

```bash
python3 -c "
import asyncio
from src.openproject_client import OpenProjectClient

async def test():
    client = OpenProjectClient()
    result = await client.test_connection()
    print('Connection test:', result)
    await client.close()

asyncio.run(test())
"
```

#### Test 2: Project Creation

```bash
python3 -c "
import asyncio
from src.openproject_client import OpenProjectClient
from src.models import ProjectCreateRequest

async def test():
    client = OpenProjectClient()
    project = ProjectCreateRequest(name='Test Project', description='Manual test')
    result = await client.create_project(project)
    print('Project created:', result.get('id'), result.get('name'))
    await client.close()

asyncio.run(test())
"
```

#### Test 3: Work Package Creation

```bash
python3 -c "
import asyncio
from src.openproject_client import OpenProjectClient
from src.models import WorkPackageCreateRequest

async def test():
    client = OpenProjectClient()
    wp = WorkPackageCreateRequest(
        project_id=YOUR_PROJECT_ID,  # Replace with actual project ID
        subject='Test Work Package',
        start_date='2024-12-20',
        due_date='2024-12-25'
    )
    result = await client.create_work_package(wp)
    print('Work package created:', result.get('id'), result.get('subject'))
    await client.close()

asyncio.run(test())
"
```

### Method 3: MCP Server Testing

#### Start the Server

```bash
python3 scripts/run_server.py
```

**Expected output:**
```
✓ Connected to OpenProject: 13.0.0
FastMCP server running...
```

#### Test Server Tools (using MCP client)

If you have an MCP client, test the tools:

1. **create_project**:
   ```json
   {
     "name": "Test Project via MCP",
     "description": "Testing MCP integration"
   }
   ```

2. **create_work_package**:
   ```json
   {
     "project_id": 123,
     "subject": "Test Task",
     "start_date": "2024-12-20",
     "due_date": "2024-12-25"
   }
   ```

3. **create_work_package_dependency**:
   ```json
   {
     "from_work_package_id": 456,
     "to_work_package_id": 457,
     "relation_type": "follows"
   }
   ```

## Claude Desktop Integration Testing

### Setup Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "python3",
      "args": ["/full/path/to/openproject-mcp-server/scripts/run_server.py"],
      "env": {
        "OPENPROJECT_URL": "http://localhost:3000",
        "OPENPROJECT_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Test Commands

Ask Claude:

1. **"Create a new project called 'AI Integration Test' with description 'Testing MCP integration'"**

2. **"In project ID X, create work packages for a simple workflow with dates"**

3. **"Create dependencies between the work packages to form a timeline"**

4. **"What projects are available?"** (if you implement the resource later)

## Verification Steps

### 1. OpenProject UI Verification

1. **Open OpenProject** in browser
2. **Navigate to Projects** → Find your test project
3. **Open Work Packages** → Verify all work packages exist
4. **Switch to Gantt view** → Verify timeline and dependencies
5. **Check dates** → Ensure start/due dates are correct

### 2. API Response Verification

Check that API responses contain:
- Project has valid ID and name
- Work packages have start/due dates
- Relations exist between work packages
- No error messages in responses

### 3. Error Handling Testing

Test error scenarios:

```bash
# Invalid API key
OPENPROJECT_API_KEY=invalid python3 scripts/test_mvp.py

# Invalid URL  
OPENPROJECT_URL=http://invalid python3 scripts/test_mvp.py

# Missing project ID
python3 -c "
from src.models import WorkPackageCreateRequest
wp = WorkPackageCreateRequest(project_id=-1, subject='Test')
print('Should validate:', wp)
"
```

## Expected Results

### ✅ Success Indicators

- All tests pass without errors
- Projects and work packages appear in OpenProject
- Gantt chart displays properly with timeline
- Dependencies show correctly in Gantt view
- MCP server starts and responds to tools
- Claude Desktop integration works

### ❌ Failure Indicators

- Connection errors to OpenProject
- API authentication failures
- Missing work packages or projects
- Gantt chart showing no timeline
- Missing dependencies between tasks
- MCP server startup errors

## Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Check OpenProject URL is accessible
   - Verify API key is correct (40 characters)
   - Ensure OpenProject API is enabled

2. **Permission Errors**:
   - Verify user has project creation permissions
   - Check work package creation permissions
   - Ensure API key user has sufficient rights

3. **Date Issues**:
   - Use YYYY-MM-DD format for dates
   - Ensure due_date is after start_date
   - Check for timezone conflicts

4. **Dependency Issues**:
   - Ensure work packages exist before creating relations
   - Verify work packages are in same project
   - Check relation type is valid

### Debug Mode

Run with debug logging:

```bash
export MCP_LOG_LEVEL=DEBUG
python3 scripts/test_mvp.py
```

### OpenProject Logs

Check OpenProject logs for API errors:
```bash
# Docker logs
docker logs openproject_app

# File logs  
tail -f /var/log/openproject/production.log
```

## Performance Testing

### Load Testing

Test with multiple concurrent operations:

```bash
# Create multiple projects
for i in {1..5}; do
  python3 -c "
import asyncio
from src.openproject_client import OpenProjectClient
from src.models import ProjectCreateRequest

async def test():
    client = OpenProjectClient()
    project = ProjectCreateRequest(name=f'Load Test {$i}')
    result = await client.create_project(project)
    print(f'Project {$i}:', result.get('id'))
    await client.close()

asyncio.run(test())
" &
done
wait
```

### Response Time Testing

Measure API response times:

```bash
time python3 scripts/test_mvp.py
```

Expected: < 30 seconds for complete MVP test

## Test Data Cleanup

After testing, clean up test data:

1. **Delete test projects** in OpenProject UI
2. **Or use API** to delete programmatically:

```bash
python3 -c "
import asyncio
from src.openproject_client import OpenProjectClient

async def cleanup():
    client = OpenProjectClient()
    projects = await client.get_projects()
    for project in projects:
        if 'Test' in project.get('name', ''):
            print(f'Found test project: {project.get('name')}')
            # Add deletion logic if needed
    await client.close()

asyncio.run(cleanup())
"
```

## Success Criteria

The MVP testing is successful when:

1. ✅ **All automated tests pass**
2. ✅ **Gantt chart displays correctly** with timeline and dependencies  
3. ✅ **Claude Desktop integration works** end-to-end
4. ✅ **Error handling works** for common failure scenarios
5. ✅ **Performance is acceptable** (< 30s for full test)

---

**Ready to test?** Start with `python3 scripts/test_mvp.py` and work through the checklist! 🚀



