"""confirm_agent.py: mcp_agent.py with a client that answers requests for
input on the terminal.

  python3 confirm_agent.py BASE_URL QUESTION python3 confirm_server.py ROOT
"""
import os, sys
import mcp_agent
from confirm_client import Asking

mcp_agent.Connection = Asking          # run() opens its connection with it

if __name__ == "__main__":
    print(mcp_agent.run(sys.argv[1], sys.argv[2], sys.argv[3:],
                        server=os.environ.get("MCP_SERVER", "files")))
