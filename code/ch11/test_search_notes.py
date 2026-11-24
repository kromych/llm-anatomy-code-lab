# test_search_notes.py -- the tool of search_notes.py offline: a stub of
# the embeddings endpoint, and mock.py in place of the model.
# Usage: python3 test_search_notes.py [BASE]   (BASE: a real chat server)
import hashlib, json, re, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import agent, mock, search_notes

def vector(text, dim=256):
    """A bag of words: each word adds one to a coordinate chosen by hash.
    The instruction in front of a query is not content and is dropped."""
    v = [0.0] * dim
    words = text.rsplit("Query:", 1)[-1].lower()
    for word in re.findall(r"[a-z0-9]+", words):
        v[hashlib.sha1(word.encode()).digest()[0]] += 1.0
    return v

class Stub(BaseHTTPRequestHandler):
    sizes = []                           # texts per embeddings request
    def do_POST(self):
        n = int(self.headers["Content-Length"])
        texts = json.loads(self.rfile.read(n))["input"]
        Stub.sizes.append(len(texts))
        out = json.dumps({"data": [{"index": i, "embedding": vector(t)}
                                   for i, t in enumerate(texts)]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)
    def log_message(self, *args):
        pass

if __name__ == "__main__":
    stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, daemon=True).start()
    search_notes.BASE = f"http://127.0.0.1:{stub.server_port}/v1"
    mock.SCRIPT[:] = [
        mock.calling("search_notes", '{"query": "cancel a generation"}'),
        mock.calling("search_notes", '{"query": "tool that may hang"}', 1),
        {"role": "assistant", "content": "Close the connection."}]
    server, base = mock.serve()
    if len(sys.argv) > 1:                # a real model, the stub as before
        base = sys.argv[1]
    task = "What do the notes say about canceling a generation?"
    answer, messages = agent.run(task, base)
    for m in messages:
        for c in m.get("tool_calls", []):
            print("call:", *c["function"].values())
        if m["role"] == "tool":
            print(m["content"], end="\n\n")
    print("answer:", answer)
    print("texts per embeddings request:", *Stub.sizes)
    server.shutdown()
    stub.shutdown()
