# OpenProject MCP Server - Usage Guide

## Overview

This document explains the correct usage of the OpenProject MCP Server tools, specifically addressing parameter type issues encountered during work package creation and how to properly format requests for AI assistants.

## Problem Encountered

When using the MCP OpenProject tools, we encountered parameter type validation errors:

```
Error: Parameter 'estimated_hours' must be one of types [number, null], got string
Error: Parameter 'parent_id' must be one of types [integer, null], got string
```

## Root Cause

The MCP tools expect specific parameter types, but the AI assistant was passing parameters as strings instead of the required types. This is a common issue when AI assistants automatically convert parameters to strings.

## Correct Parameter Types

### Work Package Creation (`mcp_openproject_create_work_package`)

| Parameter | Required Type | Example | Notes |
|-----------|---------------|---------|-------|
| `project_id` | `integer` | `3` | Must be a number, not a string |
| `subject` | `string` | `"My Work Package"` | String is correct |
| `description` | `string` | `"Description text"` | String is correct |
| `start_date` | `string` or `null` | `"2025-01-15"` | Must be YYYY-MM-DD format |
| `due_date` | `string` or `null` | `"2025-02-15"` | Must be YYYY-MM-DD format |
| `parent_id` | `integer` or `null` | `37` | Must be a number, not a string |
| `assignee_id` | `integer` or `null` | `123` | Must be a number, not a string |
| `estimated_hours` | `number` or `null` | `8.5` | Must be a number, not a string |

### Work Package Dependencies (`mcp_openproject_create_work_package_dependency`)

| Parameter | Required Type | Example | Notes |
|-----------|---------------|---------|-------|
| `from_work_package_id` | `integer` | `38` | Must be a number, not a string |
| `to_work_package_id` | `integer` | `39` | Must be a number, not a string |
| `relation_type` | `string` | `"blocks"` | String is correct |
| `description` | `string` | `"Description"` | String is correct |
| `lag` | `integer` | `0` | Must be a number, not a string |

## Correct Usage Examples

### ✅ Correct: Creating a Work Package

```json
{
  "project_id": 3,
  "subject": "Implement user authentication",
  "description": "Create login form with validation",
  "start_date": "2025-01-15",
  "due_date": "2025-01-22",
  "parent_id": 37,
  "estimated_hours": 8.5
}
```

### ❌ Incorrect: String Parameters

```json
{
  "project_id": "3",           // ❌ String instead of integer
  "parent_id": "37",           // ❌ String instead of integer
  "estimated_hours": "8.5"     // ❌ String instead of number
}
```

### ✅ Correct: Creating Dependencies

```json
{
  "from_work_package_id": 38,
  "to_work_package_id": 39,
  "relation_type": "blocks",
  "description": "User story blocks technical task",
  "lag": 0
}
```

## Available Work Package Types

The server supports the following work package types:

| ID | Name | Description |
|----|------|-------------|
| 1 | Task | Default task type |
| 2 | Milestone | Project milestone |
| 3 | Summary task | Parent task for grouping |
| 4 | Feature | Feature implementation |
| 5 | Epic | Large feature or initiative |
| 6 | User story | User story from product backlog |
| 7 | Bug | Bug report or fix |

## Available Relation Types

| Type | Description |
|------|-------------|
| `follows` | Task A follows Task B (A comes after B) |
| `precedes` | Task A precedes Task B (A comes before B) |
| `blocks` | Task A blocks Task B (A must be done before B) |
| `blocked` | Task A is blocked by Task B |
| `relates` | General relationship between tasks |
| `duplicates` | Task A duplicates Task B |
| `duplicated` | Task A is duplicated by Task B |

## Best Practices for AI Assistants

### 1. Parameter Type Validation

Always ensure parameters are passed with the correct types:

```python
# ✅ Correct
project_id = 3  # integer
estimated_hours = 8.5  # number
parent_id = 37  # integer

# ❌ Incorrect
project_id = "3"  # string
estimated_hours = "8.5"  # string
parent_id = "37"  # string
```

### 2. Date Format

Always use YYYY-MM-DD format for dates:

```python
# ✅ Correct
start_date = "2025-01-15"
due_date = "2025-02-15"

# ❌ Incorrect
start_date = "2025"  # incomplete
due_date = "15/01/2025"  # wrong format
```

### 3. Null Values

Use `null` for optional parameters, not empty strings:

```python
# ✅ Correct
parent_id = null
assignee_id = null
estimated_hours = null

# ❌ Incorrect
parent_id = ""
assignee_id = ""
estimated_hours = ""
```

## Common Workflows

### 1. Creating an Epic with User Stories and Tasks

```python
# Step 1: Create Epic
epic = create_work_package(
    project_id=3,
    subject="User Management System",
    description="Complete user management implementation"
)

# Step 2: Create User Story
story = create_work_package(
    project_id=3,
    subject="As a user, I want to login",
    description="User story description",
    parent_id=epic.id  # Link to epic
)

# Step 3: Create Technical Task
task = create_work_package(
    project_id=3,
    subject="Implement login form",
    description="Technical implementation",
    parent_id=story.id,  # Link to story
    estimated_hours=8.0
)

# Step 4: Create Dependencies
create_dependency(
    from_work_package_id=story.id,
    to_work_package_id=task.id,
    relation_type="blocks"
)
```

### 2. Project Management Structure

```
Epic (ID: 37)
├── User Story (ID: 38) - blocks → Technical Task (ID: 39)
├── User Story (ID: 40) - follows → Technical Task (ID: 39)
└── Milestone (ID: 41) - relates → Epic (ID: 37)
```

## Error Handling

### Common Errors and Solutions

1. **Parameter Type Errors**
   - **Error**: `Parameter 'X' must be one of types [Y], got string`
   - **Solution**: Convert string parameters to the required type

2. **Date Format Errors**
   - **Error**: Invalid date format
   - **Solution**: Use YYYY-MM-DD format

3. **API Key Errors**
   - **Error**: `400 Bad Request` or authentication errors
   - **Solution**: Verify API key is correctly configured

4. **Network Errors**
   - **Error**: `All connection attempts failed`
   - **Solution**: Check OpenProject URL and network connectivity

## Testing Commands

### Health Check
```bash
curl http://your-server:39128/health
```

### Manual API Test
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://your-openproject/api/v3/projects"
```

## Conclusion

The OpenProject MCP Server is a powerful tool for project management automation. The key to successful usage is ensuring all parameters are passed with the correct types. AI assistants should pay special attention to:

1. **Integer parameters**: `project_id`, `parent_id`, `assignee_id`
2. **Number parameters**: `estimated_hours`
3. **Date parameters**: Use YYYY-MM-DD format
4. **Null values**: Use `null` for optional parameters

By following these guidelines, AI assistants can effectively use the OpenProject MCP Server to create and manage complex project structures with Epics, User Stories, Tasks, and their dependencies.
