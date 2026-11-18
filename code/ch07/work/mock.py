# mock.py PORT TTFT0 GAP NCH SLOTS -- a mock streaming server for trying
# loadgen.py: every POST is answered with NCH server-sent events, TTFT0
# seconds before the first and GAP seconds between the others. SLOTS
# requests are served at a time; the others wait for a free slot.
# The run described in the book (sec:ch7-measure):
#   python3 mock.py PORT 0.05 0.01 40 4
import json, sys, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

TTFT0, GAP = float(sys.argv[2]), float(sys.argv[3])
NCH, SLOTS = int(sys.argv[4]), int(sys.argv[5])
sem = threading.Semaphore(SLOTS)

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *a):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        with sem:
            time.sleep(TTFT0)
            for i in range(NCH):
                if i:
                    time.sleep(GAP)
                d = {"choices": [{"delta": {"content": f"{i} "}}]}
                event = b"data: " + json.dumps(d).encode() + b"\n\n"
                self.wfile.write(event)
                self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()

ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
