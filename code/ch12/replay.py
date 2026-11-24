# replay.py -- send again two requests of smolagents from a proxy log.
# The first is the first one whose reply stopped at the limit of generated
# tokens: once as logged, with tool_choice "required", and once with
# tool_choice "auto". The second is the first one whose reply ended without
# a call although the request said "required": once as logged and once
# without its stop sequences.
# Usage: python3 replay.py BASE_URL LOG [capped]  (standard library only).
# LOG is a proxy log that holds the requests in full, compressed by gzip or
# plain. With the word "capped", the first request alone is sent, as logged.
import gzip, json, sys, time, urllib.request

BASE, LOG = sys.argv[1], sys.argv[2]
ALONE = sys.argv[3:] == ["capped"]
log = gzip.open(LOG, "rt") if LOG.endswith(".gz") else open(LOG)
recs = [r for r in map(json.loads, log)
        if r["tag"].startswith("smolagents") and r.get("n_tools")]

def send(label, body):
    req = urllib.request.Request(BASE + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=7200))
    secs = time.time() - t0
    c = r["choices"][0]
    text = c["message"].get("content") or ""
    calls = [t["function"]["name"]
             for t in c["message"].get("tool_calls") or []]
    print("%-22s finish %-6s tokens %5d in %6.1f s, calls %s, text of %d "
          "characters" % (label, c["finish_reason"],
                          r["usage"]["completion_tokens"], secs, calls,
                          len(text)))
    print("   ", json.dumps(text[:200]))
    print("    ...", json.dumps(text[-70:]))

def show(rec):
    print("request of", rec["tag"], "with", rec["n_messages"], "messages;",
          "logged reply:", rec["usage"]["completion_tokens"], "tokens,",
          "finish", rec["finish"])

capped = next((r for r in recs if r.get("finish") == "length"), None)
if capped is None:
    print("no capped request of smolagents in", LOG)
else:
    show(capped)
    send('tool_choice "required"', capped["request"])
    if ALONE:
        sys.exit()
    send('tool_choice "auto"', dict(capped["request"], tool_choice="auto"))

ended = next((r for r in recs if r.get("finish") == "stop"
              and not r.get("calls")), None)
if ended is None:
    print("no reply of smolagents that ended without a call in", LOG)
else:
    show(ended)
    send("as logged", ended["request"])
    send("without stop sequences",
         {k: v for k, v in ended["request"].items() if k != "stop"})
