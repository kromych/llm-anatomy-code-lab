"""Summarize one run of the porting experiment, a directory that run_exp.sh
wrote: per program, the correct answers, the requests, tokens and seconds
per task, the capped requests and the lines of code; per task, its requests
and how it ended; the first request for the Bergen question; and how far
the three repetitions agree.

Usage: python3 analyze.py RUN   (writes RUN/summary.json and RUN/tasks.tsv)
"""
import collections, json, pathlib, statistics, sys

here = pathlib.Path(__file__).parent
run = here / (sys.argv[1] if len(sys.argv) > 1 else "run")
res = [json.loads(l) for l in open(run / "results.jsonl")]
prox = [x for x in map(json.loads, open(run / "proxy-run.jsonl"))
        if x["path"].endswith("/chat/completions")]
CAP = 1024
ports = [p for p in ("baseline", "smolagents", "pydanticai",
                     "openai_agents", "dspy")
         if any(x["port"] == "port_" + p for x in res)]

def loc(port):
    lines = (here / f"port_{port}.py").read_text().splitlines()
    return sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))

def usage(q, key):
    return (q.get("usage") or {}).get(key, 0)

def cached(q):
    return (usage(q, "prompt_tokens_details") or {}).get("cached_tokens", 0)

# A request belongs to the last task of its tag that began before it.
for x in res:
    x["reqs"] = []
for q in prox:
    mine = [x for x in res if x["tag"] == q["tag"] and x["t"] <= q["t"]]
    if mine:
        max(mine, key=lambda x: x["t"])["reqs"].append(q)

def kind(y):
    """A reply by its finish reason, its text, and its calls."""
    calls = y.get("calls") or []
    return ", ".join((str(y.get("finish")),
                      "text" if y.get("reply_chars") else "no text",
                      "final_answer" if "final_answer" in calls
                      else "call" if calls else "no call"))

def ending(x):
    """How a task ended, read from its last request and the reply to it."""
    if x["error"]:
        return "error"
    last = x["reqs"][-1]
    if last["n_tools"] == 0 and any(q["n_tools"] for q in x["reqs"]):
        return "step limit"         # the framework asks once more, no tools
    if last.get("calls"):
        return "call " + "+".join(last["calls"])
    return "text" if last.get("finish") == "stop" else str(last.get("finish"))

rows, tasks = [], []
for p in ports:
    r = [x for x in res if x["port"] == f"port_{p}"]
    q = [y for x in r for y in x["reqs"]]
    n = len(r)
    pt = sum(usage(y, "prompt_tokens") for y in q)
    ct = sum(usage(y, "completion_tokens") for y in q)
    by_task = collections.defaultdict(list)
    for x in r:
        by_task[x["task"]].append(x)
        tasks.append(dict(
            port=p, rep=int(x["tag"].rsplit("-r", 1)[1]), task=x["task"],
            requests=len(x["reqs"]),
            prompt=sum(usage(y, "prompt_tokens") for y in x["reqs"]),
            completion=sum(usage(y, "completion_tokens") for y in x["reqs"]),
            capped=sum(usage(y, "completion_tokens") >= CAP
                       for y in x["reqs"]),
            secs=x["secs"], correct=x["correct"], end=ending(x),
            answer=" ".join(x["answer"].split())[:70]))
    def trace(x):
        return [(usage(y, "prompt_tokens"), usage(y, "completion_tokens"))
                for y in x["reqs"]]
    first = next(x for x in r if x["task"] == "bergen")["reqs"][0]
    rows.append(dict(
        port=p, tasks=n, correct=sum(x["correct"] for x in r),
        errors=sum(1 for x in r if x["error"]),
        requests_per_task=round(len(q) / n, 2),
        prompt_tokens_per_task=round(pt / n),
        completion_tokens_per_task=round(ct / n),
        cached_share=round(sum(cached(y) for y in q) / pt, 3),
        secs_per_task=round(statistics.mean(x["secs"] for x in r), 3),
        secs_median=round(statistics.median(x["secs"] for x in r), 3),
        capped=sum(1 for y in q if usage(y, "completion_tokens") >= CAP),
        loc=loc(p),
        ends=dict(collections.Counter(ending(x) for x in r)),
        replies=dict(collections.Counter(kind(y) for y in q)),
        requests_max=max(len(x["reqs"]) for x in r),
        prompt_tokens_max=max(usage(y, "prompt_tokens") for y in q),
        # requests by the length of their system prompt, in characters
        system_chars=dict(collections.Counter(
            y["system_chars"] for y in q)),
        # of the six questions, those whose repetitions agree
        same_tokens=sum(all(trace(x) == trace(v[0]) for x in v)
                        for v in by_task.values()),
        same_answer=sum(all(x["answer"] == v[0]["answer"] for x in v)
                        for v in by_task.values()),
        bergen_first=dict(
            bytes=first["req_bytes"], system_chars=first["system_chars"],
            prompt_tokens=usage(first, "prompt_tokens"),
            n_tools=first["n_tools"], keys=first["keys"])))
for row in rows:
    print(json.dumps(row))
json.dump(rows, open(run / "summary.json", "w"), indent=1)
with open(run / "tasks.tsv", "w") as f:
    f.write("\t".join(tasks[0]) + "\n")
    for t in tasks:
        f.write("\t".join(str(v) for v in t.values()) + "\n")
per_task = collections.defaultdict(dict)
for x in res:
    per_task[x["task"]].setdefault(x["port"][5:], []).append(x["correct"])
print({t: {p: sum(v) for p, v in d.items()} for t, d in per_task.items()})
for x in res:
    if not x["correct"]:
        print("wrong:", x["tag"], x["task"], repr(x["answer"][:90]),
              x["error"] and x["error"][:80])
