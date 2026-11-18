"""bench.py: round-trip time of tools/call over stdio and over HTTP."""
import http.client, json, statistics, sys, time
from mcp_client import Connection, P, INFO

N = 2000
CALL = {"name": "list_files", "arguments": {"path": "."}}

def stats(name, ts):
    ts = sorted(t * 1e6 for t in ts)
    print("%-28s median %6.0f us  p90 %6.0f us  p99 %6.0f us" % (
        name, statistics.median(ts), ts[int(.9*len(ts))], ts[int(.99*len(ts))]))

c = Connection([sys.executable, "files_server.py", "sample"])
t0 = time.perf_counter(); c.open(); t1 = time.perf_counter()
print("launch + discover %.1f ms" % ((t1 - t0) * 1e3))
ts = []
for i in range(N):
    t = time.perf_counter(); c.request("tools/call", CALL)
    ts.append(time.perf_counter() - t)
stats("stdio", ts[100:])
c.close()

def post(conn, rid):
    params = dict(CALL, _meta={P + "protocolVersion": "2026-07-28",
                               P + "clientCapabilities": {},
                               P + "clientInfo": INFO})
    body = json.dumps({"jsonrpc": "2.0", "id": rid,
                       "method": "tools/call", "params": params})
    conn.request("POST", "/mcp", body, {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2026-07-28",
        "Mcp-Method": "tools/call", "Mcp-Name": "list_files"})
    r = conn.getresponse(); data = r.read()
    assert r.status == 200, (r.status, data)

port = int(sys.argv[1])
conn = http.client.HTTPConnection("127.0.0.1", port)
ts = []
for i in range(N):
    t = time.perf_counter(); post(conn, i); ts.append(time.perf_counter() - t)
stats("HTTP, kept-alive connection", ts[100:])
ts = []
for i in range(N // 2):
    t = time.perf_counter()
    conn = http.client.HTTPConnection("127.0.0.1", port); post(conn, i)
    conn.close(); ts.append(time.perf_counter() - t)
stats("HTTP, new connection", ts[50:])
