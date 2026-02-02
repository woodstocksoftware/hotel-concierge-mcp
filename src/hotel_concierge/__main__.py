"""Entry point for running the MCP server."""
import sys
print("Starting MCP server...", file=sys.stderr)

try:
    from .server import mcp
    print("Import successful", file=sys.stderr)
    mcp.run(transport="stdio")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
