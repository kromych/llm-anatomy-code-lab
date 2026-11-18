"""Split the first agent request of each run into system text, tool
schemas and the rest, in tokens of the served model.

usage: python3 composition.py ENGINE log.jsonl DUMPDIR TAG...
ENGINE is the base URL of llama-server (for /tokenize)."""
import json, sys, urllib.request

engine, log, dumps, tags = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]

def ntokens(text):
    req = urllib.request.Request(engine + "/tokenize",
                                 json.dumps({"content": text}).encode(),
                                 {"Content-Type": "application/json"})
    return len(json.load(urllib.request.urlopen(req))["tokens"])

def text_of(content):
    if isinstance(content, list):
        return "".join(p.get("text", "") for p in content)
    return content or ""

records = [json.loads(line) for line in open(log)]
for tag in tags:
    run = [r for r in records if r["tag"] == tag and "n" in r]
    first = next((r for r in run if r.get("n_tools")), run[0])
    q = json.load(open("%s/%s-%02d.json" % (dumps, tag, first["n"])))
    items = q.get("messages") or q.get("input") or []
    system = (q.get("instructions") or "") + "".join(
        text_of(m.get("content")) for m in items
        if m.get("role") in ("system", "developer"))
    # llama-server skips Responses tools that are not functions
    tools = "\n".join(json.dumps(t) for t in q.get("tools") or []
                      if t.get("type") == "function")
    u = first["usage"]
    total = u.get("prompt_tokens", u.get("input_tokens"))
    s, t = ntokens(system), ntokens(tools)
    print("%-12s system %6d  tools %6d  rest %6d  total %6d" % (
        tag, s, t, total - s - t, total))
