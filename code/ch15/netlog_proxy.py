"""A forward proxy that records which hosts a program contacts.

usage: python3 netlog_proxy.py PORT LOG.jsonl

Point a program at it with HTTPS_PROXY=http://127.0.0.1:PORT (and
HTTP_PROXY), keeping the local model out with NO_PROXY=127.0.0.1,localhost.
For every connection it logs the time, the host and port, and the bytes
sent each way.  HTTPS stays encrypted end to end (CONNECT tunnels), so the
log holds no URLs, headers or contents."""
import json, select, socket, sys, threading, time

PORT, LOG = int(sys.argv[1]), sys.argv[2]
lock = threading.Lock()

def pipe(a, b):
    up = down = 0
    socks = [a, b]
    while True:
        r, _, x = select.select(socks, [], socks, 300)
        if x or not r:
            break
        for s in r:
            data = s.recv(65536)
            if not data:
                return up, down
            (b if s is a else a).sendall(data)
            if s is a:
                up += len(data)
            else:
                down += len(data)
    return up, down

def handle(c):
    t0 = time.time()
    try:
        head = b""
        while b"\r\n\r\n" not in head and len(head) < 65536:
            chunk = c.recv(4096)
            if not chunk:
                return
            head += chunk
        line = head.split(b"\r\n", 1)[0].decode(errors="replace")
        method, target = line.split(" ")[:2]
        if method == "CONNECT":
            host, port = target.rsplit(":", 1)
            s = socket.create_connection((host, int(port)), timeout=30)
            c.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            rest = head.split(b"\r\n\r\n", 1)[1]
            if rest:
                s.sendall(rest)
        else:                      # plain HTTP: absolute URI in the line
            hostport = target.split("/")[2]
            host, _, port = hostport.partition(":")
            port = port or "80"
            s = socket.create_connection((host, int(port)), timeout=30)
            s.sendall(head)
        up, down = pipe(c, s)
        rec = {"t": round(t0, 3), "method": method, "host": host,
               "port": int(port), "up": up, "down": down,
               "secs": round(time.time() - t0, 3)}
    except Exception as e:           # record failures too
        rec = {"t": round(t0, 3), "error": type(e).__name__}
    finally:
        c.close()
    with lock, open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", PORT))
srv.listen(64)
while True:
    conn, _ = srv.accept()
    threading.Thread(target=handle, args=(conn,), daemon=True).start()
