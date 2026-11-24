"""For each request of a run, the number of leading tokens that it shares
with the request before it and with the best of all earlier ones, beside
the cached tokens that the engine reported.  The requests are rendered as
the engine sees them, with llama-server's /apply-template and /tokenize.

usage: python3 prefix.py ENGINE log.jsonl DUMPDIR TAG...
ENGINE is the base URL of llama-server; the bodies are those kept by
proxy.py."""
import json, sys, urllib.error, urllib.request

engine, log, dumps = sys.argv[1], sys.argv[2], sys.argv[3]
tags = sys.argv[4:]

def post(path, body):
    req = urllib.request.Request(engine + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))

def text_of(content):
    if isinstance(content, list):
        return "".join(p.get("text", "") for p in content
                       if isinstance(p, dict))
    return content or ""

def messages_of(q):
    """Chat Completions messages and tools of a request body; the items
    of a Responses body are converted first."""
    if "messages" in q:
        return q["messages"], q.get("tools") or []
    msgs = [{"role": "system", "content": q.get("instructions") or ""}]
    thought = ""                  # a reasoning item belongs to what follows
    for item in q.get("input") or []:
        kind = item.get("type", "message")
        if kind == "reasoning":
            thought = text_of(item.get("content"))
            continue
        if kind == "message":
            role = item["role"] if item["role"] != "developer" else "system"
            msg = {"role": role, "content": text_of(item["content"])}
        elif kind == "function_call":
            msg = {"role": "assistant", "content": "", "tool_calls": [{
                "id": item["call_id"], "type": "function", "function": {
                    "name": item["name"],
                    "arguments": item["arguments"]}}]}
        elif kind == "function_call_output":
            msg = {"role": "tool", "tool_call_id": item["call_id"],
                   "content": text_of(item["output"])}
        else:
            continue
        if msg["role"] == "assistant" and thought:
            msg["reasoning_content"], thought = thought, ""
        msgs.append(msg)
    tools = [{"type": "function", "function": {
                  k: t[k] for k in ("name", "description", "parameters")
                  if k in t}}
             for t in q.get("tools") or [] if t.get("type") == "function"]
    return msgs, tools            # other kinds of tools: the engine skips

def tokens(q):
    msgs, tools = messages_of(q)
    body = {"messages": msgs}
    if tools:
        body["tools"] = tools
    prompt = post("/apply-template", body)["prompt"]
    return post("/tokenize", {"content": prompt})["tokens"]

def common(a, b):
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n

records = [json.loads(line) for line in open(log)]
for tag in tags:
    print("%s\n  n  prompt cached  tokens  previous  best earlier" % tag)
    seen = []
    for r in [r for r in records if r["tag"] == tag and "n" in r]:
        q = json.load(open("%s/%s-%02d.json" % (dumps, tag, r["n"])))
        u = r.get("usage") or {}
        used = u.get("prompt_tokens", u.get("input_tokens", 0))
        details = (u.get("prompt_tokens_details")
                   or u.get("input_tokens_details") or {})
        try:
            t = tokens(q)
        except urllib.error.HTTPError as e:
            print("%3d %7d %6d  not rendered (status %d)" % (
                r["n"], used, details.get("cached_tokens", 0), e.code))
            continue
        shared = [common(t, old) for old in seen]
        best = max(range(len(seen)), key=shared.__getitem__, default=None)
        print("%3d %7d %6d %7d %9s  %s" % (
            r["n"], used, details.get("cached_tokens", 0), len(t),
            shared[-1] if shared else "-",
            "-" if best is None else
            "%d (request %d)" % (shared[best], best + 1)))
        seen.append(t)
