# loading.py -- what a server answers while it starts: polls it with a
# small request and prints each change of the answer.  Start this
# program first and the server second.
# Usage: python3 loading.py BASE_URL MODEL   (standard library only)
import json, sys, time, urllib.request, urllib.error

BASE, MODEL = sys.argv[1], sys.argv[2]
body = json.dumps({"model": MODEL, "max_tokens": 1, "messages": [
    {"role": "user", "content": "Hi"}]}).encode()
last, t0 = None, time.time()
while True:
    req = urllib.request.Request(BASE + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            now = "status %d" % resp.status
    except urllib.error.HTTPError as e:
        now = "status %d, Retry-After=%s, %s" % (
            e.code, e.headers.get("Retry-After"), e.read()[:120].decode())
    except OSError as e:          # no listener yet
        now = "no connection"
    if now != last:
        print("%5.1f s  %s" % (time.time() - t0, now), flush=True)
        last = now
    if now == "status 200":
        break
    time.sleep(0.05)
