# evaluate.py -- run the agent on a small task set and record what happened.
import json, re, sys, time
import agent

TASKS = [  # (question, answer that must appear in the reply)
    ("Which file mentions GGUF? Give its path.", "docs/formats.md"),
    ("Which port does the server configuration set?", "9931"),
    ("What is the total of the gigabytes column of data/sizes.csv?",
     "61.5"),
    ("How many files are in the docs directory?", "3"),
    ("What is the title on the first line of README.md?", "Lab notebook"),
    ("How many lines of log/server.log contain ERROR?", "3"),
    ("Which file defines the function quantize? Give its path.",
     "src/quant.py"),
    ("What is 12 percent of the total of the gigabytes column of "
     "data/sizes.csv?", "7.38"),
]

def evaluate(base, run=agent.run, repeats=1):
    rows = []
    for q, expect in TASKS:
        for r in range(repeats):
            usage = {"prompt": 0, "cached": 0, "completion": 0, "turns": 0}
            def log(turn, reply):
                u = reply.get("usage") or {}
                usage["prompt"] += u.get("prompt_tokens", 0)
                usage["completion"] += u.get("completion_tokens", 0)
                usage["cached"] += (u.get("prompt_tokens_details") or {}
                                    ).get("cached_tokens", 0)
                usage["turns"] = turn + 1
            t0 = time.time()
            try:
                answer, _ = run(q, base, log=log)
            except Exception as e:
                answer = f"crash: {e}"
            text = (answer or "").replace(",", "")
            ok = re.search(rf"(?<![\w.]){re.escape(expect)}(?!\w|\.\d)",
                           text) is not None
            rows.append(dict(question=q, ok=ok, answer=answer,
                             seconds=round(time.time() - t0, 2), **usage))
    return rows

if __name__ == "__main__":
    rows = evaluate(sys.argv[1], repeats=int(sys.argv[2]) if
                    len(sys.argv) > 2 else 1)
    for r in rows:
        print(json.dumps(r))
    n = sum(r["ok"] for r in rows)
    print(f"solved {n} of {len(rows)}", file=sys.stderr)
