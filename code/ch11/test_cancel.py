# test_cancel.py -- cancel a streamed task of show.py, then ask again.
import _thread, json, threading, time
from http.server import ThreadingHTTPServer
import mock, show

CALL = {"role": "assistant", "tool_calls": [{
    "index": 0, "id": "call_0", "type": "function", "function": {
        "name": "read_file", "arguments": '{"path": "README.md"}'}}]}
WORDS = "The title of the file is Lab notebook".split()

class Slow(mock.Handler):
    """Stream every reply; press Ctrl-C in the middle of the second."""
    stopped = []
    def do_POST(self):
        n = int(self.headers["Content-Length"])
        Slow.received.append(json.loads(self.rfile.read(n))["messages"])
        k = len(Slow.received)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        deltas = [CALL] if k == 1 else [{"content": w + " "} for w in WORDS]
        try:
            for i, delta in enumerate(deltas, 1):
                chunk = json.dumps({"choices": [{"delta": delta}]})
                self.wfile.write(f"data: {chunk}\n\n".encode())
                time.sleep(0.05)
                if (k, i) == (2, 3):
                    _thread.interrupt_main()     # what Ctrl-C does
            self.wfile.write(b"data: [DONE]\n\n")
        except OSError:                  # the client closed the connection
            Slow.stopped.append((k, i))

server = ThreadingHTTPServer(("127.0.0.1", 0), Slow)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}/v1"
kept = show.converse(["What is the title of README.md?\n",
                      "Tell me again.\n"], base)
time.sleep(0.5)                          # let the server notice
for k, i in Slow.stopped:
    print(f"request {k}: the server stopped at chunk {i} of {len(WORDS)}")
print("request 3 held:", [m["role"] for m in Slow.received[2]])
print("conversation:", [m["role"] for m in kept])
server.shutdown()
