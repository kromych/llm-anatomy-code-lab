# status.py -- which HTTP status, error body and headers a server returns
# for an unknown model, a prompt longer than the context, and a malformed
# request; for a request that succeeds it prints the usage instead.
# Usage: python3 status.py BASE_URL MODEL   (standard library only)
import json, sys, urllib.request, urllib.error

BASE, MODEL = sys.argv[1], sys.argv[2]

def post(body):
    req = urllib.request.Request(BASE + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()

LONG = "word " * 45000           # 45,001 tokens for Qwen3, more than
                                 # the 40,960 its context holds
cases = {
    "unknown model": {"model": "no-such-model", "max_tokens": 5,
        "messages": [{"role": "user", "content": "Hi"}]},
    "prompt too long": {"model": MODEL, "max_tokens": 5,
        "messages": [{"role": "user", "content": LONG}]},
    "malformed": {"model": MODEL, "messages": "not a list"},
}
for name, body in cases.items():
    code, headers, text = post(body)
    retry = headers.get("Retry-After") or headers.get("retry-after")
    print("%-16s %d  Retry-After=%s" % (name, code, retry))
    try:
        reply = json.loads(text)
    except ValueError:
        reply = {"error": text[:120].decode("utf-8", "replace")}
    if "error" in reply:
        print("    error:", json.dumps(reply["error"])[:200])
    else:
        print("    usage:", reply.get("usage"))
