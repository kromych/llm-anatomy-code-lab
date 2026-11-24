"""lockrun.py shared|exclusive cmd... : hold badc's host load lock (turnstile protocol of
badc scripts/host_load.py) while running cmd. The lock fds are close-on-exec."""
import fcntl, pathlib, subprocess, sys, time
mode, cmd = sys.argv[1], sys.argv[2:]
home = pathlib.Path.home()
t0 = time.time()
with open(home / '.badc-load.turnstile', 'a') as ts, open(home / '.badc-load.lock', 'a') as lk:
    fcntl.flock(ts, fcntl.LOCK_EX)
    fcntl.flock(lk, fcntl.LOCK_EX if mode == 'exclusive' else fcntl.LOCK_SH)
    fcntl.flock(ts, fcntl.LOCK_UN)
    print(f"lockrun: {mode} lock after {time.time() - t0:.0f} s wait", file=sys.stderr, flush=True)
    sys.exit(subprocess.call(cmd))
