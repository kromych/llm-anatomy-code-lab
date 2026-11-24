"""Drive files_server.py with the official SDK's Client in each mode."""
import asyncio, sys
from mcp import Client, StdioServerParameters

async def run(mode):
    params = StdioServerParameters(command=sys.executable,
        args=["files_server.py", "sample"])
    async with Client(params, mode=mode) as c:
        tools = await c.list_tools()
        r = await c.call_tool("read_file", {"path": "a.txt"})
        bad = await c.call_tool("read_file", {"path": "../../etc/passwd"})
        print(mode, [t.name for t in tools.tools], repr(r.content[0].text),
              "| escape:", bad.is_error, bad.content[0].text)
        try:
            await c.call_tool("rm_rf", {})
        except Exception as e:
            print("   unknown tool ->", type(e).__name__, e)

for m in ["auto", "legacy", "2026-07-28"]:
    asyncio.run(run(m))
