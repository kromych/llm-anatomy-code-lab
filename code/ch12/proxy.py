"""Logging proxy for the seam: /<tag>/v1/... -> upstream /v1/..., one JSON
line per request with message and tool counts, sizes and token usage.

Usage: python3 proxy.py PORT UPSTREAM LOG [FULL]
With a fourth argument, every line is also written to the file FULL
together with the request and the response."""
import json, sys, threading, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT, UPSTREAM, LOGFILE = int(sys.argv[1]), sys.argv[2], sys.argv[3]
FULL = sys.argv[4] if len(sys.argv) > 4 else None
lock = threading.Lock()

def chars(content):
    """Length of a message's text, given as a string or as a list of parts."""
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(p.get("text") or "") for p in content
                   if isinstance(p, dict))
    return 0

def reply_of(data):
    """The response as JSON where it is JSON, as text otherwise."""
    try:
        return json.loads(data)
    except ValueError:
        return data.decode(errors="replace")

def usage_of(data, ctype):
    if "event-stream" in ctype:
        u = None
        for line in data.decode(errors="replace").splitlines():
            if line.startswith("data: {"):
                u = json.loads(line[6:]).get("usage") or u
        return u
    try:
        return json.loads(data).get("usage")
    except ValueError:
        return None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.forward(None)

    def do_POST(self):
        self.forward(self.rfile.read(int(self.headers.get("Content-Length", 0))))

    def forward(self, body):
        _, tag, rest = self.path.split("/", 2)
        req = urllib.request.Request(UPSTREAM + "/" + rest, data=body,
                                     method=self.command,
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req) as r:
                data, status, ctype = r.read(), r.status, r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            data, status, ctype = e.read(), e.code, e.headers.get("Content-Type", "")
        secs = time.time() - t0
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        rec = {"tag": tag, "path": "/" + rest, "status": status, "t": t0, "secs": secs,
               "req_bytes": len(body or b"")}
        if body:
            q = json.loads(body)
            msgs = q.get("messages", [])
            rec.update(n_messages=len(msgs), n_tools=len(q.get("tools") or []),
                       tools_bytes=len(json.dumps(q.get("tools") or [])),
                       stream=bool(q.get("stream")),
                       keys=sorted(q),
                       system_chars=sum(chars(m.get("content")) for m in msgs
                                        if m.get("role") in ("system", "developer")))
            if tag.endswith("-dump"):
                rec["request"] = q
        rec["usage"] = usage_of(data, ctype)
        reply = reply_of(data)
        if isinstance(reply, dict) and reply.get("choices"):
            choice = reply["choices"][0]
            msg = choice.get("message") or {}
            rec.update(finish=choice.get("finish_reason"),
                       reply_chars=chars(msg.get("content")),
                       calls=[c["function"]["name"]
                              for c in msg.get("tool_calls") or []])
        with lock:
            with open(LOGFILE, "a") as f:
                f.write(json.dumps(rec) + "\n")
            if FULL and body:
                with open(FULL, "a") as f:
                    f.write(json.dumps(dict(rec, request=q, response=reply))
                            + "\n")

    def log_message(self, *args):
        pass

ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
