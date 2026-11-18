import asyncio, sys
from mcp import Client, StdioServerParameters
mode = sys.argv[1]
async def main():
    params = StdioServerParameters(command=sys.executable,
        args=["tap.py", "results/sdk-tap-%s.log" % mode, sys.executable,
              "files_server.py", "sample"])
    async with Client(params, mode=mode) as c:
        await c.list_tools()
        await c.call_tool("read_file", {"path": "a.txt"})
asyncio.run(main())
