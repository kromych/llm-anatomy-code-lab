"""summarize.py: accuracy, turns and time per file and mode.

  python3 summarize.py numbers/results/*.jsonl calculator/results/*.jsonl
Every record is graded again from its transcript with measure.py, using
the questions.json next to the results directory.
"""
import json, os, statistics, sys
from collections import defaultdict
from measure import final_answer, grade

def reply(record):
    if record["transcript"][-1]["role"] == "error":     # engine failed
        return ""
    return record["transcript"][-1].get("content") or ""

for path in sys.argv[1:]:
    qfile = os.path.join(os.path.dirname(os.path.dirname(path)),
                         "questions.json")
    questions = {q["id"]: q for q in json.load(open(qfile))}
    groups = defaultdict(list)
    for line in open(path):
        r = json.loads(line)
        r["answer"] = final_answer(reply(r))
        r["correct"] = grade(questions[r["id"]], r["answer"])
        groups[r["mode"]].append(r)
    for mode, rs in groups.items():
        runs = sorted({r["run"] for r in rs})
        per_run = [sum(r["correct"] for r in rs if r["run"] == k)
                   for k in runs]
        errors = sum(r["transcript"][-1]["role"] == "error" for r in rs)
        print("%s %s: correct %s of %d; no answer %d (%d errors); "
              "turns %.1f; "
              "calls %.1f; median %.1f s; mean %.1f s; tokens %.0f" % (
                  path, mode, "+".join(map(str, per_run)),
                  len(rs) // len(runs),
                  sum(r["answer"] is None for r in rs), errors,
                  statistics.mean(r["turns"] for r in rs),
                  statistics.mean(r["tool_calls"] for r in rs),
                  statistics.median(r["seconds"] for r in rs),
                  statistics.mean(r["seconds"] for r in rs),
                  statistics.mean(r["tokens"] for r in rs)))
