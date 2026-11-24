#!/usr/bin/env python3
"""Benign probes of a sandbox (Chapter 16).

usage: battery.py ROOT PORT

ROOT holds work/ (the policy lets us write there) with a directory
work/.git/hooks (the policy should protect it), outside/ and
secret/token.txt, a dummy secret; PORT is a listener on 127.0.0.1
that answers each connection with "battery-listener".  The probes
touch nothing else.  Each prints its name, ALLOWED or BLOCKED, and
the error by which the sandbox showed itself.  The child that the
last probe leaves behind writes work/orphan.txt a second later, if
it is still alive; the runner looks for that file.
"""
import errno
import os
import socket
import subprocess
import sys

root, port = sys.argv[1], int(sys.argv[2])


def control():              # write inside the workspace: must work
    with open(os.path.join(root, "work", "ok.txt"), "w") as f:
        f.write("ok\n")


def write():                # write outside the workspace
    with open(os.path.join(root, "outside", "probe.txt"), "w") as f:
        f.write("escaped\n")


def read():                 # read the dummy secret
    with open(os.path.join(root, "secret", "token.txt")) as f:
        f.read()


def net():                  # reach the listener on the host
    with socket.create_connection(("127.0.0.1", port), timeout=3) as s:
        if not s.recv(64).startswith(b"battery-listener"):
            raise ConnectionError("not our listener")


def spawn():                # start a child process
    subprocess.run(["/bin/sh", "-c", "exit 0"], check=True)


def hook():                 # write a git hook inside the workspace
    path = os.path.join(root, "work", ".git", "hooks", "pre-commit")
    with open(path, "w") as f:
        f.write("escaped\n")


def orphan():               # leave a child behind, in its own session
    marker = os.path.join(root, "work", "orphan.txt")
    code = "import sys, time; time.sleep(1); open(sys.argv[1], 'w')"
    subprocess.Popen([sys.executable, "-c", code, marker],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


for name, probe in [("control", control), ("write", write),
                    ("read", read), ("net", net), ("spawn", spawn),
                    ("hook", hook), ("orphan", orphan)]:
    try:
        probe()
        print(f"{name:8}ALLOWED")
    except Exception as e:
        code = errno.errorcode.get(getattr(e, "errno", None), "")
        print(f"{name:8}BLOCKED  {type(e).__name__} {code}")
