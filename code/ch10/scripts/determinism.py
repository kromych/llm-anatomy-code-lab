# determinism.py -- is the same request answered the same way twice?
# Sends one request at temperature 0 several times, with and without
# another request in between, and prints the length of each answer and
# a checksum of its text.
# Usage: python3 determinism.py BASE_URL MODEL   (standard library only)
import json, sys, urllib.request, zlib

BASE, MODEL = sys.argv[1], sys.argv[2]
Q = "Is 91 a prime number? Answer in one word."

def ask(text, seed=None):
    body = {"model": MODEL, "temperature": 0, "max_tokens": 1500,
            "messages": [{"role": "user", "content": text}]}
    if seed is not None:
        body["seed"] = seed
    req = urllib.request.Request(BASE + "/chat/completions",
            json.dumps(body).encode(),
            {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        r = json.load(resp)
    m = r["choices"][0]["message"]
    text = (m.get("reasoning_content") or m.get("reasoning") or "") + \
        (m.get("content") or "")
    cached = (r["usage"].get("prompt_tokens_details") or {}).get(
        "cached_tokens")
    return "%4d tokens, checksum %08x, %s prompt tokens cached" % (
        r["usage"]["completion_tokens"], zlib.crc32(text.encode()), cached)

for label, seed in (("no seed", None), ("seed 7", 7)):
    print(label)
    for k in range(3):
        print("  repeated         ", ask(Q, seed))
    for k in range(3):
        ask("Count to three.", seed)          # another prompt in between
        print("  after another one", ask(Q, seed))
