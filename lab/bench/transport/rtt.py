#!/usr/bin/env python3
"""rtt.py -- round-trip time of a small message over the transports of
Figure 1.5 (Chapter 1), measured from Python, the language in which most of
the stack's glue is written (MCP SDKs, vLLM, SGLang, agent frameworks).

    python3 rtt.py [-n 2000] [--only call,tcp,...] [--remote HOST]  > out.csv
    python3 rtt.py --serve tcp|http 0.0.0.0:PORT     (server for LAN tests)

Each test sends a 64-byte message and waits for the same 64 bytes back. A
test runs 200 untimed round trips, then N timed ones; it prints the median
and the 10th and 90th percentiles in microseconds. Round trips shorter
than a microsecond are timed in batches of 1000, so their percentiles are
over batch means. Servers run as child processes of this script, so every
test except `call` and `ctypes` crosses a process boundary. Optional
tests (zmq, dbus, llama, ollama, remote, internet) are skipped when their
module or server is missing.
"""
import argparse, ctypes, http.client, os, platform, socket, statistics
import subprocess, sys, tempfile, time

MSG = b"x" * 63 + b"\n"
WARM = 200


def pct(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))]


def report(name, samples_ns, note=""):
    us = [s / 1000 for s in samples_ns]
    print(f"{name},{len(us)},{statistics.median(us):.3f},"
          f"{pct(us, 0.10):.3f},{pct(us, 0.90):.3f},{note}", flush=True)


def timed(fn, n):
    for _ in range(WARM):
        fn()
    out = []
    for _ in range(n):
        t = time.perf_counter_ns()
        fn()
        out.append(time.perf_counter_ns() - t)
    return out


def batched(fn, n, b=1000):
    for _ in range(WARM):
        fn()
    out = []
    for _ in range(max(20, n // 50)):
        t = time.perf_counter_ns()
        for _ in range(b):
            fn()
        out.append((time.perf_counter_ns() - t) / b)
    return out


# ------------------------------------------------------------------ servers
def serve(kind, addr):
    """Run one echo server; print 'ready' when it accepts connections."""
    if kind == "stdio":
        inp, out = sys.stdin.buffer, sys.stdout.buffer
        out.write(b"ready\n"); out.flush()
        for line in iter(inp.readline, b""):
            out.write(line); out.flush()
        return
    if kind in ("tcp", "unix"):
        fam = socket.AF_UNIX if kind == "unix" else socket.AF_INET
        s = socket.socket(fam, socket.SOCK_STREAM)
        if kind == "tcp":
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            host, port = addr.rsplit(":", 1)
            s.bind((host, int(port)))
        else:
            s.bind(addr)
        s.listen(1)
        print("ready", flush=True)
        while True:
            c, _ = s.accept()
            if kind == "tcp":
                c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            f = c.makefile("rb")
            for line in iter(f.readline, b""):
                c.sendall(line)
            c.close()
    if kind in ("http", "sse"):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class H(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            def log_message(self, *a):
                pass
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                if self.path == "/sse":   # one event, chunked, as servers stream
                    ev = b"data: " + body.strip() + b"\n\n"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    self.wfile.write(b"%x\r\n%s\r\n0\r\n\r\n" % (len(ev), ev))
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                self.wfile.flush()
        ThreadingHTTPServer.daemon_threads = True
        host, port = addr.rsplit(":", 1)
        srv = ThreadingHTTPServer((host, int(port)), H)
        srv.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print("ready", flush=True)
        srv.serve_forever()
    if kind == "zmq":
        import zmq
        s = zmq.Context().socket(zmq.REP)
        s.bind(addr)
        print("ready", flush=True)
        while True:
            s.send(s.recv())
    if kind == "mpconn":
        from multiprocessing.connection import Listener
        with Listener(addr, authkey=b"rtt") as lst:
            print("ready", flush=True)
            with lst.accept() as c:
                while True:
                    try:
                        c.send_bytes(c.recv_bytes())
                    except EOFError:
                        return
    if kind == "shm":
        from multiprocessing import shared_memory
        try:
            m = shared_memory.SharedMemory(name=addr, track=False)
        except TypeError:          # Python < 3.13
            m = shared_memory.SharedMemory(name=addr)
        b = m.buf
        print("ready", flush=True)
        while True:            # spin: 1 = request ready, 2 = reply ready
            while b[0] != 1:
                if b[1] == 9:
                    m.close(); return
            b[72:136] = b[8:72]
            b[0] = 2


def child(kind, addr, **kw):
    p = subprocess.Popen([sys.executable, os.path.abspath(__file__),
                          "--serve", kind, addr], stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE if kind == "stdio" else None,
                         bufsize=0, **kw)
    assert p.stdout.readline().strip() == b"ready"
    return p


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]; s.close()
    return port


# ------------------------------------------------------------------- tests
def t_call(n):
    def echo(m):
        return m
    report("call", batched(lambda: echo(MSG), n), "Python function call")


def t_ctypes(n):
    lib = ctypes.cdll.msvcrt if os.name == "nt" else ctypes.CDLL(None)
    f = lib.labs
    f.argtypes, f.restype = [ctypes.c_long], ctypes.c_long
    report("ctypes", batched(lambda: f(-7), n), "C function through ctypes")


def t_shm(n):
    from multiprocessing import shared_memory
    m = shared_memory.SharedMemory(create=True, size=256)
    b = m.buf
    b[0] = b[1] = 0
    p = child("shm", m.name)
    def rt():
        b[8:72] = MSG
        b[0] = 1
        while b[0] != 2:
            pass
        b[0] = 0
    report("shm", timed(rt, n), "shared memory, both sides spinning")
    b[1] = 9; p.wait(); m.close(); m.unlink()


def t_stdio(n):
    p = child("stdio", "-")
    def rt():
        p.stdin.write(MSG)
        p.stdout.readline()
    report("stdio", timed(rt, n), "child process, line over stdin/stdout")
    p.stdin.close(); p.wait()


def stream_test(name, fam, addr, conn_addr, n, note):
    p = child(name if name != "tcp" else "tcp", addr)
    s = socket.socket(fam, socket.SOCK_STREAM)
    s.connect(conn_addr)
    if fam == socket.AF_INET:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    f = s.makefile("rb")
    def rt():
        s.sendall(MSG)
        f.readline()
    report(name, timed(rt, n), note)
    s.close(); p.terminate(); p.wait()


def t_unix(n):
    if not hasattr(socket, "AF_UNIX") or os.name == "nt":
        return
    path = os.path.join(tempfile.mkdtemp(), "rtt.sock")
    stream_test("unix", socket.AF_UNIX, path, path, n, "Unix domain socket")
    os.unlink(path)


def t_tcp(n):
    port = free_port()
    stream_test("tcp", socket.AF_INET, f"127.0.0.1:{port}",
                ("127.0.0.1", port), n, "TCP on loopback, TCP_NODELAY")


def t_mpconn(n):
    from multiprocessing.connection import Client
    if os.name == "nt":
        addr, note = r"\\.\pipe\rtt-%d" % os.getpid(), "Windows named pipe"
    else:
        addr = os.path.join(tempfile.mkdtemp(), "mp.sock")
        note = "multiprocessing.connection (Unix socket)"
    p = child("mpconn", addr)
    c = Client(addr, authkey=b"rtt")
    def rt():
        c.send_bytes(MSG)
        c.recv_bytes()
    report("mpconn", timed(rt, n), note)
    c.close(); p.wait()


def http_rt(conn, path):
    conn.request("POST", path, body=MSG,
                 headers={"Content-Type": "application/octet-stream"})
    r = conn.getresponse()
    r.read()


def t_http(n):
    port = free_port()
    p = child("http", f"127.0.0.1:{port}")
    conn = http.client.HTTPConnection("127.0.0.1", port)
    report("http", timed(lambda: http_rt(conn, "/echo"), n),
           "HTTP/1.1 keep-alive, Python http.server")
    report("sse", timed(lambda: http_rt(conn, "/sse"), n),
           "same, response is one chunked SSE event")
    conn.close(); p.terminate(); p.wait()


def t_zmq(n):
    try:
        import zmq
    except ImportError:
        return
    ctx = zmq.Context()
    addrs = [("zmq-tcp", f"tcp://127.0.0.1:{free_port()}")]
    if os.name != "nt":
        addrs.append(("zmq-ipc", "ipc://" + os.path.join(tempfile.mkdtemp(),
                                                         "z.sock")))
    for name, addr in addrs:
        p = child("zmq", addr)
        s = ctx.socket(zmq.REQ)
        s.connect(addr)
        def rt():
            s.send(MSG)
            s.recv()
        report(name, timed(rt, n), f"ZeroMQ REQ/REP, pyzmq {zmq.__version__}")
        s.close(linger=0); p.terminate(); p.wait()


def t_dbus(n):
    try:
        from jeepney import DBusAddress, new_method_call
        from jeepney.io.blocking import open_dbus_connection
    except ImportError:
        return
    try:
        conn = open_dbus_connection(bus="SYSTEM")
    except Exception:
        return
    peer = DBusAddress("/org/freedesktop/DBus", bus_name="org.freedesktop.DBus",
                       interface="org.freedesktop.DBus.Peer")
    msg = lambda: conn.send_and_get_reply(new_method_call(peer, "Ping"))
    report("dbus", timed(msg, n), "D-Bus Peer.Ping to the system bus daemon")
    conn.close()


def t_get(name, host, port, path, n, note):
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET", path); conn.getresponse().read()
    except OSError:
        return
    def rt():
        conn.request("GET", path)
        conn.getresponse().read()
    report(name, timed(rt, n), note)
    conn.close()


def t_llama(n):
    t_get("llama-server", "127.0.0.1", int(os.environ.get("LLAMA_PORT", 8091)),
          "/health", n, "GET /health, llama-server (C++)")


def t_ollama(n):
    t_get("ollama", "127.0.0.1", 11434, "/api/version", n,
          "GET /api/version, Ollama (Go)")


def t_remote(n, host):
    """LAN: tcp and http echo servers started on HOST beforehand with --serve."""
    h, tport, hport = host.split(":")
    s = socket.create_connection((h, int(tport)))
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    f = s.makefile("rb")
    def rt():
        s.sendall(MSG)
        f.readline()
    report("lan-tcp", timed(rt, n), f"TCP echo on {h}")
    s.close()
    conn = http.client.HTTPConnection(h, int(hport))
    report("lan-http", timed(lambda: http_rt(conn, "/echo"), n),
           f"HTTP/1.1 keep-alive to {h}")
    conn.close()


def t_internet(n, hosts=("huggingface.co", "github.com")):
    for h in hosts:
        conn = http.client.HTTPSConnection(h, timeout=10)
        def rt():
            conn.request("HEAD", "/")
            conn.getresponse().read()
        try:
            report(f"https-{h}", timed_small(rt, n), "HEAD / on a kept-alive "
                   "HTTPS connection")
        except OSError:
            pass
        conn.close()


def timed_small(fn, n):     # few round trips: these leave the lab
    fn(); fn()
    out = []
    for _ in range(n):
        t = time.perf_counter_ns(); fn(); out.append(time.perf_counter_ns() - t)
        time.sleep(0.2)
    return out


TESTS = ["call", "ctypes", "shm", "stdio", "unix", "mpconn", "tcp", "zmq",
         "http", "dbus", "llama", "ollama"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=2000)
    ap.add_argument("--only")
    ap.add_argument("--remote", help="HOST:TCPPORT:HTTPPORT of --serve'd echo")
    ap.add_argument("--internet", type=int, default=0,
                    help="also time N HTTPS requests to two public hosts")
    ap.add_argument("--serve", nargs=2, metavar=("KIND", "ADDR"))
    a = ap.parse_args()
    if a.serve:
        return serve(*a.serve)
    print(f"# {platform.node()} {platform.platform()} {platform.machine()} "
          f"Python {platform.python_version()} "
          f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}"
          + (" load %.2f %.2f %.2f" % os.getloadavg()
             if hasattr(os, "getloadavg") else ""))
    print("test,n,median_us,p10_us,p90_us,note")
    only = a.only.split(",") if a.only else (TESTS if not a.remote else [])
    for t in only:
        globals()["t_" + t](a.n)
    if a.remote:
        t_remote(a.n, a.remote)
    if a.internet:
        t_internet(a.internet)


if __name__ == "__main__":
    main()
