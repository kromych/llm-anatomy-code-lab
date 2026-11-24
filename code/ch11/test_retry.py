# Exercise the retry wrapper against mock.py with injected failures.
import json, time
import agent, mock, retry

FAIL = [(503, {"Retry-After": "2"}), (429, {}), (500, {})]

class Flaky(mock.Handler):
    def do_POST(self):
        if FAIL:
            code, headers = FAIL.pop(0)
            n = int(self.headers["Content-Length"]); self.rfile.read(n)
            if code == "drop":           # close without answering
                return
            if code == "cut":            # promise 100 bytes, send 10
                self.send_response(200)
                self.send_header("Content-Length", "100")
                self.end_headers()
                self.wfile.write(b'{"choices"')
                return
            self.send_response(code)
            for k, v in headers.items():
                self.send_header(k, v)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        super().do_POST()

mock.SCRIPT[:] = [{"role": "assistant", "content": "Lab notebook"}]
from http.server import ThreadingHTTPServer
import threading
server = ThreadingHTTPServer(("127.0.0.1", 0), Flaky)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}/v1"
agent.chat = retry.patient(agent.chat, first=0.5)
t0 = time.time()
answer, _ = agent.run("What is the title of README.md?", base)
print("answer:", answer, f"after {time.time() - t0:.1f} s")
# a client error is not retried
FAIL[:] = [(400, {})]
try:
    agent.run("again", base)
except Exception as e:
    print("raised:", e)
# a connection that drops before or during the reply is retried
FAIL[:] = [("drop", {}), ("cut", {})]
t0 = time.time()
answer, _ = agent.run("again", base)
print("answer:", answer, f"after {time.time() - t0:.1f} s")
# a refused connection is retried, then raised
server.shutdown(); server.server_close()
t0 = time.time()
try:
    agent.run("again", base)
except Exception as e:
    print("raised:", e, f"after {time.time() - t0:.1f} s")
