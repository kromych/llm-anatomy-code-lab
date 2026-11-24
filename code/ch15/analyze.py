"""Summarize the proxy log of Chapter 15, one line per tag (one run).

usage: python3 analyze.py log.jsonl [tag-suffix]

For every run: requests, the system text and tools of the largest request,
the prompt tokens of the first agent request, and the totals of prompt,
cached and generated tokens as the engine reported them."""
import collections, json, sys

def tokens(u):
    u = u or {}
    p = u.get("prompt_tokens", u.get("input_tokens", 0))
    c = u.get("completion_tokens", u.get("output_tokens", 0))
    d = u.get("prompt_tokens_details") or u.get("input_tokens_details") or {}
    return p, c, d.get("cached_tokens", 0)

runs = collections.OrderedDict()
for line in open(sys.argv[1]):
    r = json.loads(line)
    if len(sys.argv) > 2 and not r["tag"].endswith(sys.argv[2]):
        continue
    if r.get("model") is not None:          # skip GET requests
        runs.setdefault(r["tag"], []).append(r)

print("%-14s %4s %6s %5s %6s %6s %7s %7s %6s %6s" % (
    "run", "req", "system", "tools", "toolkB", "first", "prompt",
    "cached", "gen", "secs"))
for tag, rs in runs.items():
    agent = [r for r in rs if r.get("n_tools")] or rs
    big = max(agent, key=lambda r: r.get("system_chars", 0))
    first = tokens(agent[0].get("usage"))[0]
    p = c = k = 0
    for r in rs:
        a, b, d = tokens(r.get("usage"))
        p, c, k = p + a, c + b, k + d
    print("%-14s %4d %6d %5d %6.1f %6d %7d %7d %6d %6.0f" % (
        tag, len(rs), big.get("system_chars", 0), big.get("n_tools", 0),
        big.get("tools_bytes", 0) / 1000, first, p, k, c,
        sum(r["secs"] for r in rs)))
