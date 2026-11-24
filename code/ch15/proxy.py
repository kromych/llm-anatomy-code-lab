"""Logging proxy for Chapter 15: /<tag>/<path> -> UPSTREAM/<path>.

Streams responses through unchanged, writes one JSON line per request with
the sizes that matter for context assembly (system text, tools, messages)
and the token counts the engine reports, and keeps every request body in
full (DUMPDIR/tag-NN.json) for later study."""
import http.client, json, os, sys, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT, UPSTREAM, LOGFILE, DUMPDIR = (int(sys.argv[1]), sys.argv[2],
                                    sys.argv[3], sys.argv[4])
os.makedirs(DUMPDIR, exist_ok=True)
up = urllib.parse.urlsplit(UPSTREAM)
lock, count = threading.Lock(), {}

def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):     # parts: {"type": "text", "text": ...}
        return "".join(p.get("text", "") for p in content
                       if isinstance(p, dict))
    return ""

def summarize(q):
    msgs = q.get("messages") or []
    items = q.get("input") if isinstance(q.get("input"), list) else []
    tools = q.get("tools") or []
    names = [t.get("function", t).get("name") for t in tools
             if isinstance(t, dict)]
    system = sum(len(text_of(m.get("content"))) for m in msgs
                 if m.get("role") in ("system", "developer"))
    system += len(q.get("instructions") or "")
    system += sum(len(text_of(i.get("content"))) for i in items
                  if isinstance(i, dict)
                  and i.get("role") in ("system", "developer"))
    return dict(model=q.get("model"), stream=bool(q.get("stream")),
                n_messages=len(msgs) or len(items), n_tools=len(tools),
                tools=names, tools_bytes=len(json.dumps(tools)),
                system_chars=system, keys=sorted(q))

def usage_in(raw):
    """Last usage/timings object found in a JSON body or an SSE stream."""
    usage = timings = None
    for line in raw.decode(errors="replace").splitlines():
        line = line[6:] if line.startswith("data: ") else line
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        resp = obj.get("response") if isinstance(obj.get("response"),
                                                  dict) else {}
        usage = obj.get("usage") or resp.get("usage") or usage
        timings = obj.get("timings") or timings
    return usage, timings

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.forward(None)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self.forward(self.rfile.read(n))

    def forward(self, body):
        _, tag, rest = self.path.split("/", 2)
        conn = http.client.HTTPConnection(up.hostname, up.port,
                                          timeout=3600)
        t0 = time.time()
        conn.request(self.command, "/" + rest, body=body,
                     headers={"Content-Type": "application/json"})
        r = conn.getresponse()
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in ("transfer-encoding", "content-length",
                                 "connection"):
                self.send_header(k, v)
        self.send_header("Connection", "close")
        self.end_headers()
        raw = bytearray()
        while chunk := r.read1(65536):
            raw += chunk
            self.wfile.write(chunk)
            self.wfile.flush()
        rec = {"tag": tag, "path": "/" + rest, "status": r.status, "t": t0,
               "secs": round(time.time() - t0, 3),
               "req_bytes": len(body or b"")}
        if body:
            q = json.loads(body)
            rec.update(summarize(q))
            with lock:
                n = count[tag] = count.get(tag, 0) + 1
            dump = os.path.join(DUMPDIR, "%s-%02d.json" % (tag, n))
            with open(dump, "w") as f:
                json.dump(q, f, indent=1)
            rec["n"] = n
        rec["usage"], rec["timings"] = usage_in(bytes(raw))
        with lock, open(LOGFILE, "a") as f:
            f.write(json.dumps(rec) + "\n")

    def log_message(self, *args):
        pass

ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
