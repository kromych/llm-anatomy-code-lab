# overload.py -- more simultaneous requests than a server has slots: are
# they queued or refused?  Prints the status of each request in the
# order in which the answers arrived.
# Usage: python3 overload.py BASE_URL MODEL [REQUESTS]
# (standard library only; REQUESTS is 8 unless given)
import json, sys, threading, time, urllib.request, urllib.error

BASE, MODEL = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 8
done, lock, t0 = [], threading.Lock(), time.time()

def one(k):
    body = {"model": MODEL, "max_tokens": 200, "temperature": 0,
            "messages": [{"role": "user", "content":
                          "Tell story number %d. /no_think" % k}]}
    req = urllib.request.Request(BASE + "/chat/completions",
            json.dumps(body).encode(),
            {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            code, retry = resp.status, resp.headers.get("Retry-After")
            tokens = json.load(resp)["usage"]["completion_tokens"]
    except urllib.error.HTTPError as e:
        code, retry, tokens = e.code, e.headers.get("Retry-After"), 0
    with lock:
        done.append((time.time() - t0, k, code, retry, tokens))

threads = [threading.Thread(target=one, args=(k,)) for k in range(N)]
for t in threads:
    t.start()
for t in threads:
    t.join()
for seconds, k, code, retry, tokens in done:
    print("request %d: status %d, Retry-After=%s, %d tokens, after "
          "%.1f s" % (k, code, retry, tokens, seconds))
