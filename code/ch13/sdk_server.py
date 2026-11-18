"""sdk_server.py: the reference server, written with the official SDK."""
import os, sys
from mcp.server.mcpserver import MCPServer

ROOT = os.path.realpath(sys.argv[1] if len(sys.argv) > 1 else ".")
app = MCPServer("sdk-files")

@app.tool()
def list_files(path: str = ".") -> str:
    """List the entries of a directory under the root."""
    p = os.path.realpath(os.path.join(ROOT, path))
    return "\n".join(sorted(os.listdir(p)))

if __name__ == "__main__":
    app.run()          # stdio by default
