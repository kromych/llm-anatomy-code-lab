# hook_probe.py -- what may the process that runs this do?  Try to create
# a file outside the workspace and to reach a port on the loopback
# interface; print the outcome and append it to a log.
# Usage: python3 hook_probe.py LABEL LOG FILE PORT     (also as a hook)
import json, os, socket, sys

label, log, path, port = sys.argv[1:5]
out = {"as": label}
try:
    open(path, "w").close()
    os.remove(path)
    out["write"] = "ok"
except OSError as e:
    out["write"] = e.strerror
try:
    socket.create_connection(("127.0.0.1", int(port)), 2).close()
    out["connect"] = "ok"
except OSError as e:
    out["connect"] = e.strerror or str(e)
print(json.dumps(out), file=sys.stderr)
try:
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(out) + "\n")
except OSError:
    pass
