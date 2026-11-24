"""files_server.py: an MCP server with two tools, standard library only.

The client starts it as  python3 files_server.py ROOT  and talks to it over
stdin and stdout, one JSON-RPC message per line.  It speaks the stateless
revision 2026-07-28 and, for older clients, the initialize handshake.
"""
import json, os, sys

MODERN = ["2026-07-28"]
LEGACY = ["2025-11-25", "2025-06-18", "2025-03-26"]
P = "io.modelcontextprotocol/"            # prefix of the _meta keys
INFO = {"name": "files", "version": "1.0"}
ROOT = os.path.realpath(sys.argv[1] if len(sys.argv) > 1 else ".")

def schema(required):
    return {"type": "object", "additionalProperties": False,
            "properties": {"path": {"type": "string"}},
            "required": required}

TOOLS = [
    {"name": "list_files", "title": "List files",
     "description": "List the entries of a directory under the root.",
     "inputSchema": schema([]), "annotations": {"readOnlyHint": True}},
    {"name": "read_file", "title": "Read a file",
     "description": "Return the text of a file under the root.",
     "inputSchema": schema(["path"]),
     "annotations": {"readOnlyHint": True}},
]

class RpcError(Exception):
    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.error = {"code": code, "message": message}
        if data is not None:
            self.error["data"] = data

def inside(rel):
    """Resolve rel against ROOT; refuse paths that leave it."""
    path = os.path.realpath(os.path.join(ROOT, rel))
    if os.path.commonpath([ROOT, path]) != ROOT:
        raise PermissionError(rel + ": outside the root")
    return path

def call_tool(name, args):
    if name not in ("list_files", "read_file"):
        raise RpcError(-32602, "Unknown tool: " + str(name))
    try:
        rel = args.get("path", ".")
        if not isinstance(rel, str):
            raise ValueError("path must be a string")
        if name == "list_files":
            text = "\n".join(sorted(os.listdir(inside(rel))))
        else:
            if "path" not in args:
                raise ValueError("path is required")
            with open(inside(rel), errors="replace") as f:
                text = f.read(100_000)
    except (OSError, ValueError) as e:     # reported to the model
        if getattr(e, "strerror", None):   # str(e) of an OSError would
            e = "%s: %s" % (rel, e.strerror)    # show the resolved path
        return {"content": [{"type": "text", "text": str(e)}],
                "isError": True}
    return {"content": [{"type": "text", "text": text}], "isError": False}

legacy = None              # the version agreed by initialize, if any

def handle(msg):
    """Algorithm O: answer one message; None for a notification."""
    global legacy
    method, params = msg.get("method"), msg.get("params") or {}
    if (msg.get("jsonrpc") != "2.0" or not isinstance(method, str)
            or msg.get("id", 0) is None):       # MCP: no null id
        raise RpcError(-32600, "Invalid request")
    if "id" not in msg:                                         # O1
        return None
    if method == "initialize":                                  # O2
        asked = params.get("protocolVersion")
        legacy = asked if asked in LEGACY else LEGACY[0]
        return {"protocolVersion": legacy, "serverInfo": INFO,
                "capabilities": {"tools": {}}}
    if legacy is None:                                          # O3
        meta = params.get("_meta") or {}
        v = meta.get(P + "protocolVersion")
        if v is None or P + "clientCapabilities" not in meta:
            raise RpcError(-32602, "Missing _meta fields")
        if v not in MODERN:
            raise RpcError(-32022, "Unsupported protocol version",
                           {"supported": MODERN, "requested": v})
    if method == "server/discover":                             # O4
        result = {"supportedVersions": MODERN,
                  "capabilities": {"tools": {}}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        result = call_tool(params.get("name"),
                           params.get("arguments") or {})
    elif method == "ping" and legacy:    # removed in 2026-07-28
        result = {}
    else:
        raise RpcError(-32601, "Method not found: " + method)
    if legacy is None:                                          # O5
        if method in ("server/discover", "tools/list"):
            result.update(ttlMs=3600_000, cacheScope="public")
        result["resultType"] = "complete"
        result["_meta"] = {P + "serverInfo": INFO}
    return result

def respond(line):
    """Turn one line of input into one line of output, or None."""
    try:
        msg = json.loads(line)
    except ValueError:
        msg = None
    if not isinstance(msg, dict):
        return {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": "Parse error"}}
    try:
        result = handle(msg)
    except RpcError as e:
        if "id" not in msg:
            return None
        return {"jsonrpc": "2.0", "id": msg["id"], "error": e.error}
    except Exception as e:            # a bug: report it, keep serving
        if "id" not in msg:
            return None
        return {"jsonrpc": "2.0", "id": msg["id"], "error":
                {"code": -32603, "message": "Internal error: %s" % e}}
    if result is None:
        return None
    return {"jsonrpc": "2.0", "id": msg["id"], "result": result}

def main():
    for line in sys.stdin:            # ends when the client closes stdin
        if not line.strip():
            continue
        out = respond(line)
        if out is not None:
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
