#!/usr/bin/env python3
"""
Run the OpenProject MCP Server

This script starts the FastMCP server for OpenProject integration.
"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

if __name__ == "__main__":
    try:
        from mcp_server import app
        # Run the FastMCP app directly - it handles its own event loop
        app.run()
    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)



