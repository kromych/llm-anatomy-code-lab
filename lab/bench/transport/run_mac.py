#!/usr/bin/env python3
"""run_mac.py -- run the transport benchmarks on the shared lab Mac.

    python3 run_mac.py VENV_PYTHON XPC_BINARY MODEL.gguf [BENCH_LOCK_DIR]

Another workload on this machine takes ~/.badc-load.lock shared for its
jobs, passing through ~/.badc-load.turnstile first. The script follows
the same protocol as an exclusive holder (turnstile, then the lock
exclusively, then the turnstile released), so that new jobs wait behind
it, and holds the lock while it measures. It then takes the lab's
benchmark lock (a directory created atomically), so that no other
measurement runs at the same time, waits up to three minutes for the load
to fall, and writes results/krom1u-rtt.csv (with the XPC line appended)
and results/krom1u-mmap.csv.
"""
import fcntl, os, subprocess, sys, time

py, xpc, model = sys.argv[1:4]
bench = sys.argv[4] if len(sys.argv) > 4 else None
here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
os.makedirs("results", exist_ok=True)

turnstile = open(os.path.expanduser("~/.badc-load.turnstile"), "a")
lock = open(os.path.expanduser("~/.badc-load.lock"), "a")
fcntl.flock(turnstile, fcntl.LOCK_EX)
fcntl.flock(lock, fcntl.LOCK_EX)
fcntl.flock(turnstile, fcntl.LOCK_UN)
print("badc lock taken", time.strftime("%T"), os.getloadavg(), flush=True)
if bench:
    while True:
        try:
            os.mkdir(bench)
            break
        except FileExistsError:
            time.sleep(15)
print("bench lock taken", time.strftime("%T"), flush=True)
try:
    t0 = time.time()
    while os.getloadavg()[0] > 8 and time.time() - t0 < 180:
        time.sleep(10)
    print("start", time.strftime("%T"), os.getloadavg(), flush=True)
    env = dict(os.environ, LLAMA_PORT="8091")
    with open("results/krom1u-rtt.csv", "w") as f:
        subprocess.run([py, "rtt.py", "-n", "5000", "--internet", "20"],
                       stdout=f, env=env, check=True)
        f.flush()
        subprocess.run([xpc, "5000"], stdout=f, check=True)
    with open("results/krom1u-mmap.csv", "w") as f:
        subprocess.run([py, "mmap_pagein.py", model, "-k", "2000"],
                       stdout=f, check=True)
    print("done", time.strftime("%T"), os.getloadavg(), flush=True)
finally:
    if bench:
        os.rmdir(bench)
    fcntl.flock(lock, fcntl.LOCK_UN)
