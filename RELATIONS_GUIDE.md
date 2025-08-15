# Work Package Relations Guide

## Overview

The OpenProject MCP Server now supports comprehensive work package relations functionality, allowing you to create dependencies between work packages for effective project planning and Gantt chart visualization.

## Features

### Supported Relation Types

The implementation supports all OpenProject relation types:

1. **follows** - Creates a chronological dependency where one work package follows another
2. **precedes** - The reverse of follows (automatically set by OpenProject)
3. **blocks** - Indicates that one work package blocks another from proceeding
4. **blocked** - The reverse of blocks
5. **relates** - Creates a general relationship without dependency
6. **duplicates** - Indicates that one work package duplicates another
7. **duplicated** - The reverse of duplicates

### Key Components

1. **Enhanced OpenProject Client** (`src/openproject_client.py`)
   - `create_work_package_relation()` - Create relations with full API compliance
   - `get_work_package_relations()` - Retrieve all relations for a work package
   - `delete_work_package_relation()` - Remove relations

2. **Updated Data Models** (`src/models.py`)
   - `WorkPackageRelation` - Complete relation data model
   - `WorkPackageRelationCreateRequest` - Request validation model

3. **MCP Server Tools** (`src/mcp_server.py`)
   - `create_work_package_dependency` - User-friendly relation creation
   - `get_work_package_relations` - Retrieve and format relations
   - `delete_work_package_relation` - Remove relations
   - `openproject://work-package-relations/{id}` - Resource endpoint

## Usage Examples

### Creating a "Follows" Relation

```python
# Work Package 456 follows Work Package 123
result = await create_work_package_dependency(
    from_work_package_id=456,  # The dependent task
    to_work_package_id=123,    # The prerequisite task
    relation_type="follows",
    description="Design must be completed before development starts",
    lag=1  # 1 working day between finish and start
)
```

### Creating Different Relation Types

```python
# Blocking relation
await create_work_package_dependency(
    from_work_package_id=123,
    to_work_package_id=456,
    relation_type="blocks",
    description="Security review blocks deployment"
)

# General relation
await create_work_package_dependency(
    from_work_package_id=123,
    to_work_package_id=456,
    relation_type="relates",
    description="These tasks are related but not dependent"
)
```

### Retrieving Relations

```python
# Get all relations for a work package
relations = await get_work_package_relations(work_package_id=123)
```

### Using the Resource Endpoint

Access relations via MCP resource:
```
openproject://work-package-relations/123
```

## API Compliance

The implementation follows the official OpenProject API v3 specification:

- **Endpoint**: `POST /api/v3/work_packages/{id}/relations`
- **Authentication**: Basic auth with API key
- **Payload Structure**:
  ```json
  {
    "type": "follows",
    "description": "Optional description",
    "lag": 0,
    "_links": {
      "to": {
        "href": "/api/v3/work_packages/{target_id}"
      }
    }
  }
  ```

## Relation Parameters

### Required Parameters
- `from_work_package_id` - Source work package ID
- `to_work_package_id` - Target work package ID

### Optional Parameters
- `relation_type` - Defaults to "follows"
- `description` - Human-readable description
- `lag` - Working days between predecessor finish and successor start (default: 0)

## Validation Rules

1. **Work Package IDs** must be positive integers
2. **Self-relations** are not allowed (from_id cannot equal to_id)
3. **Relation types** must be from the supported list
4. **Lag** must be zero or positive (working days)

## Error Handling

The implementation provides comprehensive error handling:

- **Validation Errors**: Input validation with clear error messages
- **API Errors**: OpenProject API errors with detailed response data
- **Network Errors**: HTTP request failures with retry suggestions

## Testing

Run the comprehensive test suite:

```bash
python test_relations.py
```

The test script validates:
- API connectivity
- Relation creation across all types
- Relation retrieval
- Relation deletion
- Input validation
- Error handling

## Gantt Chart Integration

Relations created through this system automatically appear in OpenProject's Gantt charts:

1. **Dependencies** are visualized as arrows between work packages
2. **Lag times** adjust the spacing between dependent tasks
3. **Critical paths** are highlighted based on relations
4. **Timeline conflicts** are detected and flagged

## Best Practices

### 1. Use Descriptive Relations
```python
await create_work_package_dependency(
    from_work_package_id=design_task_id,
    to_work_package_id=development_task_id,
    relation_type="follows",
    description="Development cannot start until design is approved",
    lag=2  # Allow 2 days for review
)
```

### 2. Plan for Lag Times
- Include buffer time for reviews, approvals, or handoffs
- Consider weekends and holidays in working day calculations
- Use lag times to model realistic project timelines

### 3. Avoid Circular Dependencies
- The system doesn't prevent circular dependencies
- Plan your relations to maintain logical flow
- Use the relations viewer to verify dependency chains

### 4. Regular Cleanup
- Remove obsolete relations when work packages are completed
- Update relations when project scope changes
- Monitor for broken relations after work package deletions

## Troubleshooting

### Common Issues

1. **"Work package cannot have a relation with itself"**
   - Ensure from_id and to_id are different

2. **"Invalid relation type"**
   - Use only supported relation types: follows, precedes, blocks, blocked, relates, duplicates, duplicated

3. **"OpenProject API error: 422"**
   - Check that both work packages exist
   - Verify you have permission to create relations
   - Ensure the relation doesn't already exist

4. **"Lag must be zero or positive"**
   - Use only non-negative integers for lag days

### Performance Considerations

- Batch relation operations when creating multiple relations
- Use `get_work_package_relations()` to check existing relations before creating new ones
- Monitor API rate limits when processing large numbers of relations

## Integration with Other Tools

The relations feature integrates seamlessly with:

- **Project status reports** - Relations are included in dependency analysis
- **Resource management** - Dependency chains help with resource allocation
- **Risk assessment** - Critical path analysis identifies potential bottlenecks
- **Timeline planning** - Automated scheduling based on dependencies

## Future Enhancements

Potential improvements for future versions:

1. **Batch Operations** - Create/update multiple relations in a single API call
2. **Dependency Validation** - Automatic circular dependency detection
3. **Template Relations** - Save and reuse common dependency patterns
4. **Visual Dependency Editor** - Interactive relation management interface
5. **Critical Path Analysis** - Automated critical path identification and reporting

## Support

For issues or questions about the relations feature:

1. Check the test script output for specific error messages
2. Verify OpenProject permissions and API connectivity
3. Review the OpenProject API v3 documentation for additional details
4. Use the MCP server health check tool to verify system status
