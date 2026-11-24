import asyncio, sys
from mcp import Client
async def main(mode):
    async with Client(sys.argv[1], mode=mode) as c:
        tools = await c.list_tools()
        r = await c.call_tool("list_files", {})
        print(mode, [t.name for t in tools.tools], repr(r.content[0].text))
for m in ["auto", "2026-07-28"]:
    asyncio.run(main(m))
