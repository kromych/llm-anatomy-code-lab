# determinism.py -- send one recorded smolagents request several times at
# temperature 0, first without llama-server's prefix cache and then with
# it, and compare the outputs and the log probabilities of the generated
# tokens with those of the first run, which computed the whole prompt.
# Usage: python3 determinism.py BASE_URL [RUNS [LOG]]  (standard library
# only). LOG is a proxy log that holds the requests in full, compressed by
# gzip or plain; of the requests of smolagents in it, the one with the
# longest reply that ended below the limit of generated tokens is sent.
import gzip, hashlib, json, sys, urllib.request

BASE = sys.argv[1]
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 4
LOG = sys.argv[3] if len(sys.argv) > 3 else "proxy.jsonl"
CAP = 1024
log = gzip.open(LOG, "rt") if LOG.endswith(".gz") else open(LOG)
rec = max((r for r in map(json.loads, log)
           if r["tag"].startswith("smolagents") and "request" in r
           and r["usage"]["completion_tokens"] < CAP),
          key=lambda r: r["usage"]["completion_tokens"])
print("request of", rec["tag"], "with", len(rec["request"]["messages"]),
      "messages and", rec["usage"]["prompt_tokens"], "prompt tokens;",
      "logged reply:", rec["usage"]["completion_tokens"], "tokens")
body = dict(rec["request"], temperature=0, seed=1, max_tokens=300,
            logprobs=True)

def send(cache):
    b = dict(body, cache_prompt=cache)
    req = urllib.request.Request(BASE + "/chat/completions",
                                 json.dumps(b).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=600))
    m = r["choices"][0]["message"]
    out = json.dumps([m.get("content"), m.get("tool_calls") and
                      [c["function"] for c in m["tool_calls"]]])
    lps = [t["logprob"] for t in r["choices"][0]["logprobs"]["content"]]
    cached = r["usage"].get("prompt_tokens_details", {}).get("cached_tokens")
    return hashlib.sha1(out.encode()).hexdigest()[:8], lps, cached

first = None
for cache in (False, True):
    for _ in range(RUNS):
        h, lps, cached = send(cache)
        first = first or lps
        same = sum(a == b for a, b in zip(lps, first))
        print("cache %-5s cached %5s output %s tokens %3d, logprobs equal "
              "to the first run's: %3d, first logprob %.9f" %
              (cache, cached, h, len(lps), same, lps[0]), flush=True)
