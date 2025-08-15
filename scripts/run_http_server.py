#!/usr/bin/env python3
"""
Run the OpenProject MCP Server in HTTP mode

This script starts the FastMCP server for OpenProject integration in HTTP mode.
"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

if __name__ == "__main__":
    try:
        from mcp_server import app
        # Run the FastMCP app in HTTP mode on port 8080
        print("Starting OpenProject MCP Server in HTTP mode on port 8080...")
        app.run(transport="sse", host="0.0.0.0", port=8080)
    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)
