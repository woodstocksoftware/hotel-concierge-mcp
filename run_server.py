#!/usr/bin/env python
"""Run the Hotel Concierge MCP server."""
import sys
sys.path.insert(0, '/Users/james/projects/hotel-concierge-mcp')

from src.hotel_concierge.server import mcp
mcp.run(transport="stdio")
