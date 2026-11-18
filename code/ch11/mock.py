# mock.py -- a scripted Chat Completions server for deterministic tests.
import json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def calling(name, arguments, i=0):
    return {"role": "assistant", "content": None, "tool_calls": [{
        "id": f"call_{i}", "type": "function",
        "function": {"name": name, "arguments": arguments}}]}

SCRIPT = [calling("read", '{"path": "README.md"}', 0),      # no such tool
          calling("read_file", '{"path": "README.md"', 1),  # broken JSON
          calling("read_file", '{"file": "README.md"}', 2), # wrong name
          calling("read_file", '{"path": "../etc/passwd"}', 3),
          {"role": "assistant", "content": "Lab notebook"}]

class Handler(BaseHTTPRequestHandler):
    received = []
    def do_POST(self):
        n = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(n))
        Handler.received.append(body["messages"])
        msg = SCRIPT[min(len(Handler.received), len(SCRIPT)) - 1]
        out = json.dumps({"choices": [{"message": msg}],
                          "usage": {"prompt_tokens": 0,
                                    "completion_tokens": 0}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)
    def log_message(self, *args):
        pass

def serve():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}/v1"

if __name__ == "__main__":
    import agent
    server, base = serve()
    answer, messages = agent.run("What is the title of README.md?", base)
    for m in messages:
        if m["role"] == "tool":
            print(m["content"])
    print("answer:", answer)
    server.shutdown()
