#!/usr/bin/env python3
"""A TCP listener on 127.0.0.1 for the battery (Chapter 16).

usage: listener.py PORTFILE LOG
Writes its port to PORTFILE, answers every connection with
"battery-listener" and appends one line per connection to LOG.
"""
import socket
import sys

srv = socket.create_server(("127.0.0.1", 0))
with open(sys.argv[1], "w") as f:
    f.write(str(srv.getsockname()[1]))
while True:
    conn, addr = srv.accept()
    with conn, open(sys.argv[2], "a") as log:
        conn.sendall(b"battery-listener\n")
        log.write(f"{addr[0]}:{addr[1]}\n")
