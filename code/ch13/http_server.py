"""http_server.py: files_server.py over Streamable HTTP (2026-07-28 only).

  python3 http_server.py ROOT [PORT]   serves http://127.0.0.1:PORT/mcp
"""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import files_server as fs              # takes ROOT from sys.argv[1]

PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
ORIGINS = {"http://127.0.0.1:%d" % PORT, "http://localhost:%d" % PORT}
STATUS = {-32700: 400, -32600: 400, -32601: 404, -32602: 400,
          -32020: 400, -32021: 400, -32022: 400}

def check_headers(h, msg):             # the headers mirror the body
    params = msg.get("params") or {}
    meta = params.get("_meta") or {}
    want = {"MCP-Protocol-Version": meta.get(fs.P + "protocolVersion"),
            "Mcp-Method": msg.get("method")}
    if msg.get("method") in ("tools/call", "prompts/get"):
        want["Mcp-Name"] = params.get("name")
    for name, value in want.items():
        if h.get(name) != value:          # header names ignore case
            raise fs.RpcError(-32020, "Header mismatch: " + name)

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"       # keep connections open

    def reply(self, status, body=None):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(status)
        if body is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin is not None and origin not in ORIGINS:
            return self.reply(403)              # DNS rebinding defense
        if self.path != "/mcp":
            return self.reply(404)
        body = self.rfile.read(int(self.headers["Content-Length"]))
        try:
            msg = json.loads(body)
            if "id" not in msg:                 # a notification
                return self.reply(202)
            if msg.get("method") == "initialize":
                raise fs.RpcError(-32022, "Unsupported protocol version",
                    {"supported": fs.MODERN, "requested":
                     (msg.get("params") or {}).get("protocolVersion")})
            check_headers(self.headers, msg)
        except fs.RpcError as e:
            return self.reply(400, {"jsonrpc": "2.0",
                                    "id": msg.get("id"), "error": e.error})
        except (ValueError, AttributeError):
            return self.reply(400, {"jsonrpc": "2.0", "id": None, "error":
                              {"code": -32700, "message": "Parse error"}})
        out = fs.respond(body)
        code = out.get("error", {}).get("code")
        self.reply(STATUS.get(code, 200), out)

    def do_GET(self):                   # no standalone stream, no
        self.reply(405)                 # sessions in this revision
    do_DELETE = do_GET

    def log_message(self, *args):       # keep stdout and stderr quiet
        pass

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
