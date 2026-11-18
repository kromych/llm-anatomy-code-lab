# summarize_more.py -- the numbers of the last sections of Chapter 17: two
# harnesses on the same problems, one GGUF file in two engines, two judges,
# and our agent with and without a hint.
# usage: python3 summarize_more.py OUT RESULTS
import glob, json, math, os, sys
from collections import defaultdict
from inspect_ai.log import read_eval_log
from analyze import lmeval_samples, mcnemar_p, wilson

def inspect_log(path):
    files = glob.glob(f"{path}/*.eval")
    log = read_eval_log(files[0]) if files else None
    return log if log and log.status == "success" else None

def by_id(log):
    return {s.id: (s.scores["last_number_match"].value == "C",
                   s.output.completion) for s in log.samples}

def paired(a, b):                        # a, b: id -> bool
    n = len(a)
    lost = sum(a[i] and not b[i] for i in a)
    gained = sum(b[i] and not a[i] for i in a)
    return n, lost, gained, mcnemar_p(lost, gained)

def main(out, res):
    lines = []
    # two harnesses: lm-eval's full run against Inspect, first 100
    lm = lmeval_samples(out, "chat-Q8_0", "gsm8k_chat", "number")
    for name in ("t0-parallel-1", "t0-serial-1"):
        log = inspect_log(f"{out}/inspect-{name}")
        if log:
            ins = {i: ok for i, (ok, _) in by_id(log).items()}
            lm100 = {i: bool(lm[i - 1]) for i in ins}   # Inspect ids from 1
            lines.append(f"lm-eval vs Inspect {name}: lm-eval "
                         f"{sum(lm100.values())}, Inspect "
                         f"{sum(ins.values())}, paired {paired(lm100, ins)}")
    # one file in two engines
    a, b = (inspect_log(f"{out}/inspect-{x}-t0-1") for x in ("ollama", "blob"))
    if a and b:
        ra, rb = by_id(a), by_id(b)
        same = sum(ra[i][1] == rb[i][1] for i in ra)
        n, lost, gained, p = paired({i: v[0] for i, v in ra.items()},
                                    {i: v[0] for i, v in rb.items()})
        lines.append(f"Ollama {sum(v[0] for v in ra.values())}, llama-server "
                     f"{sum(v[0] for v in rb.values())}, identical replies "
                     f"{same}, Ollama only {lost}, llama-server only "
                     f"{gained}, McNemar p {p:.3f}")
    # judges
    for f in sorted(glob.glob(f"{out}/judge-*.jsonl")):
        rows = [json.loads(l) for l in open(f)]
        n = len(rows)
        if not n:
            continue
        first = sum(r["right_first"] == "A" for r in rows)
        second = sum(r["right_second"] == "B" for r in rows)
        both = sum(r["right_first"] == "A" and r["right_second"] == "B"
                   for r in rows)
        says_a = sum((r["right_first"] == "A") + (r["right_second"] == "A")
                     for r in rows)
        other = sum((r["right_first"] not in "AB") +
                    (r["right_second"] not in "AB") for r in rows)
        lines.append(f"judge {rows[0]['judge']}: pairs {n}, right first "
                     f"{first}, right second {second}, both {both}, "
                     f"verdicts A {says_a} of {2 * n}, unparsed {other}")
    # agent
    for h in ("false", "true"):
        log = inspect_log(f"{out}/agent-hint-{h}")
        if not log:
            continue
        per = defaultdict(list)
        for s in log.samples:
            per[s.input].append(s.scores["whole_word"].value == "C")
        total = sum(sum(v) for v in per.values())
        lines.append(f"agent hint={h}: solved {total} of "
                     f"{sum(len(v) for v in per.values())}; per task "
                     f"{[sum(v) for v in per.values()]}")
        turns = [s.metadata.get("turns") for s in log.samples]
        lines.append(f"  turns {sorted(turns)}")
    os.makedirs(res, exist_ok=True)
    with open(f"{res}/summary-more.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
