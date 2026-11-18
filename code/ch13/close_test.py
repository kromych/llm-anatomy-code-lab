"""close_test.py: what does a server answer when its input closes?

  python3 close_test.py RUNS CMD...

Writes four requests to the standard input of the server CMD, closes the
input at once, and prints the ids of the responses that arrive before the
server exits.
"""
import json, subprocess, sys

P = "io.modelcontextprotocol/"
META = {P + "protocolVersion": "2026-07-28", P + "clientCapabilities": {},
        P + "clientInfo": {"name": "close_test.py", "version": "1.0"}}
CALL = {"name": "list_files", "arguments": {"path": "."}}
REQUESTS = [("server/discover", {}), ("tools/list", {}),
            ("tools/call", CALL), ("tools/call", CALL)]

def run(argv):
    lines = "".join(json.dumps({
        "jsonrpc": "2.0", "id": i, "method": method,
        "params": dict(params, _meta=META)}) + "\n"
        for i, (method, params) in enumerate(REQUESTS, 1))
    p = subprocess.run(argv, input=lines, capture_output=True, text=True,
                       timeout=60)        # communicate() closes stdin
    ids = [json.loads(line).get("id") for line in p.stdout.splitlines()]
    return ids, p.returncode

if __name__ == "__main__":
    for k in range(int(sys.argv[1])):
        ids, status = run(sys.argv[2:])
        print("run %d: responses for ids %s, exit status %d"
              % (k + 1, ids, status))
