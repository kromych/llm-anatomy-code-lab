"""sdk1_server.py: a legacy server written with SDK 1.x (FastMCP)."""
import os, sys
from mcp.server.fastmcp import FastMCP
ROOT = os.path.realpath(sys.argv[1] if len(sys.argv) > 1 else ".")
app = FastMCP("legacy-files")
@app.tool()
def list_files(path: str = ".") -> str:
    """List the entries of a directory under the root."""
    return "\n".join(sorted(os.listdir(os.path.join(ROOT, path))))
if __name__ == "__main__":
    app.run()
