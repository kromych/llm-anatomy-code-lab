"""tap.py LOG CMD...: run CMD, copying its stdin and stdout lines to LOG."""
import subprocess, sys, threading, time
log = open(sys.argv[1], "w", buffering=1)
t0 = time.perf_counter()
p = subprocess.Popen(sys.argv[2:], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, text=True)
def up():
    for line in sys.stdin:
        log.write("%9.3f -> %s" % ((time.perf_counter()-t0)*1e3, line))
        p.stdin.write(line); p.stdin.flush()
    p.stdin.close()
threading.Thread(target=up, daemon=True).start()
for line in p.stdout:
    log.write("%9.3f <- %s" % ((time.perf_counter()-t0)*1e3, line))
    sys.stdout.write(line); sys.stdout.flush()
p.wait()
