"""cite_check.py: classify the URLs in an agent's answer by what it read.

  python3 cite_check.py results/run-qwen3-8b.jsonl
For each recorded run (search_run.py), every URL in the final answer is
"read" if fetch_page returned it, "seen" if it appeared only in search
results, and "unseen" if no tool result in the session contained it.
"""
import json, re, sys

URL = re.compile(r"https?://[^\s)\]>`'\"*]+")

def norm(u):
    u = u.rstrip(".,;:")
    scheme, _, rest = u.partition("://")
    host, slash, path = rest.partition("/")
    return host.lower() + "/" + path.rstrip("/")

def classify(run):
    read, seen = set(), set()
    for m in run["transcript"]:
        if m["role"] != "tool":
            continue
        first = m["content"].split("\n", 1)[0]
        if first.startswith("UNTRUSTED PAGE TEXT from "):
            read.add(norm(first.split()[4].rstrip(",")))
        seen.update(norm(u) for u in URL.findall(m["content"]))
    answer = run["transcript"][-1].get("content") or ""
    out = []
    for u in dict.fromkeys(URL.findall(answer)):
        n = norm(u)
        out.append((u, "read" if n in read else
                       "seen" if n in seen else "unseen"))
    return out

if __name__ == "__main__":
    for i, line in enumerate(open(sys.argv[1]), 1):
        run = json.loads(line)
        print("run %d (%s):" % (i, run["date"]))
        for u, kind in classify(run) or [("(no URL in the answer)", "")]:
            print("  %-6s %s" % (kind, u))
