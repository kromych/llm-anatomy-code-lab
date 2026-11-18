# reasoning.py -- where a server puts the reasoning of a thinking model:
# the string fields of the message and of the stream's deltas, and the
# usage, with thinking on and switched off in three ways.
# Usage: python3 reasoning.py BASE_URL MODEL [FILE]  (standard library
# only; FILE receives the first response as JSON)
import json, sys, urllib.request
from stream import sse_events

BASE, MODEL = sys.argv[1], sys.argv[2]
Q = "Is 91 a prime number? Answer in one word."
CASES = [("thinking on", Q, {}),
         ("/no_think in the message", Q + " /no_think", {}),
         ("enable_thinking false", Q,
          {"chat_template_kwargs": {"enable_thinking": False}}),
         ("reasoning_effort none", Q, {"reasoning_effort": "none"})]

def post(body):
    body = dict({"model": MODEL, "temperature": 0, "max_tokens": 1500},
                **body)
    req = urllib.request.Request(BASE + "/chat/completions",
            json.dumps(body).encode(),
            {"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=600)

def strings(d):
    """The non-empty string fields of a message or delta: their lengths."""
    return {k: len(v) for k, v in d.items()
            if isinstance(v, str) and v and k != "role"}

for label, text, extra in CASES:
    body = dict({"messages": [{"role": "user", "content": text}]},
                **extra)
    with post(body) as resp:
        r = json.load(resp)
    if label == "thinking on" and len(sys.argv) > 3:
        json.dump(r, open(sys.argv[3], "w"), indent=1)
    m = r["choices"][0]["message"]
    print(label)
    print("  message", strings(m), "answer", repr(m["content"][-12:]))
    print("  usage  ", r["usage"])
    runs = []           # the fields of the deltas, in order of arrival
    with post(dict(body, stream=True)) as resp:
        for d in sse_events(resp):
            if d == "[DONE]":
                break
            for c in json.loads(d).get("choices") or []:
                for k in strings(c.get("delta") or {}):
                    if not runs or runs[-1][0] != k:
                        runs.append([k, 0])
                    runs[-1][1] += 1
    print("  stream ", ", ".join("%d %s" % (n, k) for k, n in runs))
