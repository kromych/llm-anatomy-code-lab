# localhost.py -- why localhost is slower than 127.0.0.1 on Windows: time a
# refused connection to ::1 and urllib requests to both names, against an
# HTTP server bound to 127.0.0.1 only (Appendix A, troubleshooting).
import socket, time, urllib.request, http.server, threading
srv = http.server.HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
print("getaddrinfo(localhost):", [a[4][0] for a in socket.getaddrinfo("localhost", port, type=socket.SOCK_STREAM)])
t = time.perf_counter()
try:
    socket.create_connection(("::1", port), timeout=10)
except OSError as e:
    print(f"connect [::1]: {type(e).__name__} after {1000*(time.perf_counter()-t):.0f} ms")
for host in ("127.0.0.1", "localhost"):
    t = time.perf_counter()
    urllib.request.urlopen(f"http://{host}:{port}/", timeout=10).read()
    print(f"urlopen {host}: {1000*(time.perf_counter()-t):.0f} ms")
srv.shutdown()
