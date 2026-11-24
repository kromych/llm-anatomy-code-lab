# stub.py -- try cachetest.py without a model: a stand-in for llama-server
# on 127.0.0.1:8080 that answers every request with made-up "timings"
# (nothing cached the first time, 9000 tokens cached afterward) and then
# runs cachetest.py against itself. Run it in this directory.
import http.server, json, runpy, threading

class H(http.server.BaseHTTPRequestHandler):
    n = 0

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        H.n += 1
        first = H.n == 1
        t = {"cache_n": 0 if first else 9000,
             "prompt_n": 9020 if first else 20, "prompt_ms": 1234.5}
        out = json.dumps({"timings": t, "choices": []}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass

s = http.server.HTTPServer(("127.0.0.1", 8080), H)
threading.Thread(target=s.serve_forever, daemon=True).start()
runpy.run_path("cachetest.py")
s.shutdown()
