"""Summarize a proxy log (proxy.py or proxy_messages.py), one line per run,
for both dialects: Chat Completions and the Anthropic Messages API.

usage: python3 analyze_messages.py ENGINE log.jsonl DUMPDIR [tag-prefix]

ENGINE is the base URL of llama-server, used for /tokenize to split the
first agent request into system text, tool schemas and the rest.

The two dialects count cached tokens differently: Chat Completions reports
prompt_tokens with the cached part inside it, the Messages API reports
input_tokens without it and the cached part in cache_read_input_tokens.
Here 'prompt' always means the whole prompt, cached part included."""
import collections, json, sys, urllib.request

engine, log, dumps = sys.argv[1], sys.argv[2], sys.argv[3]
prefix = sys.argv[4] if len(sys.argv) > 4 else ""

def tokens(u):
    """(whole prompt, cached part, generated) for either dialect."""
    u = u or {}
    if "input_tokens" in u and "prompt_tokens" not in u:
        cached = u.get("cache_read_input_tokens", 0) or 0
        return u["input_tokens"] + cached, cached, u.get("output_tokens", 0)
    d = u.get("prompt_tokens_details") or {}
    return (u.get("prompt_tokens", 0), d.get("cached_tokens", 0),
            u.get("completion_tokens", 0))

def ntokens(text):
    req = urllib.request.Request(engine + "/tokenize",
                                 json.dumps({"content": text}).encode(),
                                 {"Content-Type": "application/json"})
    return len(json.load(urllib.request.urlopen(req))["tokens"])

def text_of(content):
    if isinstance(content, list):
        return "".join(p.get("text", "") for p in content
                       if isinstance(p, dict))
    return content or ""

def composition(q):
    msgs = q.get("messages") or []
    system = text_of(q.get("system")) + "".join(
        text_of(m.get("content")) for m in msgs
        if m.get("role") in ("system", "developer"))
    tools = "\n".join(json.dumps(t) for t in q.get("tools") or [])
    return ntokens(system), ntokens(tools)

runs = collections.OrderedDict()
for line in open(log):
    r = json.loads(line)
    if r.get("model") is None or not r["tag"].startswith(prefix):
        continue                          # GET requests, other runs
    if r["path"].endswith("/count_tokens"):
        continue                          # counting, not generating
    runs.setdefault(r["tag"], []).append(r)

print("%-16s %4s %6s %5s %6s %6s %6s %6s %7s %7s %6s" % (
    "run", "req", "system", "tools", "toolkB", "first", "sys_t", "tool_t",
    "prompt", "cached", "gen"))
for tag, rs in runs.items():
    agent = [r for r in rs if r.get("n_tools")] or rs
    big = max(agent, key=lambda r: r.get("system_chars", 0))
    first = agent[0]
    q = json.load(open("%s/%s-%02d.json" % (dumps, tag, first["n"])))
    s_t, t_t = composition(q)
    p = k = c = 0
    for r in rs:
        a, b, g = tokens(r.get("usage"))
        p, k, c = p + a, k + b, c + g
    print("%-16s %4d %6d %5d %6.1f %6d %6d %6d %7d %7d %6d" % (
        tag, len(rs), big.get("system_chars", 0), big.get("n_tools", 0),
        big.get("tools_bytes", 0) / 1000, tokens(first.get("usage"))[0],
        s_t, t_t, p, k, c))
