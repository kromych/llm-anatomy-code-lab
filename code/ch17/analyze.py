# analyze.py -- turn the raw logs of run_all.sh into the numbers of
# Chapter 17: Wilson intervals, run-to-run spread, pass@k (Algorithm Y)
# and paired comparisons of quantizations.
# usage: python3 analyze.py OUT RESULTS
import glob, json, math, os, re, statistics, sys
from collections import Counter, defaultdict
from inspect_ai.log import read_eval_log

Z = 1.96

def wilson(c, n):
    p = c / n
    d = 1 + Z * Z / n
    mid = (p + Z * Z / (2 * n)) / d
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return mid - half, mid + half

def pass_at_k(n, c, k):          # Algorithm Y
    if c == 0:
        return 0.0
    if n - c < k:
        return 1.0
    q = 1.0
    for i in range(n - c + 1, n + 1):
        q *= 1 - k / i
    return 1 - q

def mcnemar_p(b, c):             # exact two-sided test on discordant pairs
    m = b + c
    tail = sum(math.comb(m, j) for j in range(min(b, c) + 1)) / 2 ** m
    return min(1.0, 2 * tail)

def inspect_runs(out):
    runs = {}
    for d in sorted(glob.glob(f"{out}/inspect-*")):
        files = glob.glob(f"{d}/*.eval")
        if not files:
            continue
        log = read_eval_log(files[0])
        if log.status != "success":         # still running, or failed
            continue
        runs[os.path.basename(d)[8:]] = {
            s.id: (s.scores["last_number_match"].value == "C",
                   s.output.completion, s.target) for s in log.samples}
    return runs

def last_number(text):             # the rule of gsm.py
    found = re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)
    return found[-1].replace(",", "") if found else None

def lmeval_samples(out, name, task, filt):
    f = glob.glob(f"{out}/lmeval-{name}/*/samples_{task}_*.jsonl")[0]
    rows = [json.loads(l) for l in open(f)]
    if filt == "number":           # last number, compared as a number
        res = {}
        for r in rows:
            if r["filter"] == "strict-match":
                a = last_number(r["resps"][0][0])
                t = r["target"].split("#### ")[-1].replace(",", "")
                res[r["doc_id"]] = int(a is not None
                                       and float(a) == float(t))
        return res
    return {r["doc_id"]: r["exact_match"] for r in rows
            if r["filter"] == filt}

def main(out, res):
    os.makedirs(res, exist_ok=True)
    lines = []
    # ------------------------------------------------ repeated runs
    runs = inspect_runs(out)
    with open(f"{res}/variance.csv", "w") as f:
        f.write("condition,run,correct,n,accuracy,lo,hi\n")
        for name, s in runs.items():
            cond, run = name.rsplit("-", 1)
            c, n = sum(v[0] for v in s.values()), len(s)
            lo, hi = wilson(c, n)
            f.write(f"{cond},{run},{c},{n},{c/n:.3f},{lo:.3f},{hi:.3f}\n")
    groups = defaultdict(list)
    for name in runs:
        groups[name.rsplit("-", 1)[0]].append(name)
    for cond, names in sorted(groups.items()):
        accs = [sum(v[0] for v in runs[x].values()) for x in names]
        texts = [{i: v[1] for i, v in runs[x].items()} for x in names]
        same = sum(all(t[i] == texts[0][i] for t in texts)
                   for i in texts[0])
        sd = statistics.stdev(accs) if len(accs) > 1 else 0
        lines.append(f"{cond}: correct per run {accs}, mean "
                     f"{statistics.mean(accs):.1f}, sd {sd:.2f}; "
                     f"identical replies in all runs: {same}")
    if "t07-seed-1" in runs and "t07-seed-1-again" in runs:
        a, b = runs["t07-seed-1"], runs["t07-seed-1-again"]
        lines.append("seed 1 twice: identical replies "
                     f"{sum(a[i][1] == b[i][1] for i in a)} of {len(a)}")
    # ------------------------------------------------ pass@k from 10 seeds
    seeds = [runs[f"t07-seed-{s}"] for s in range(1, 11)
             if f"t07-seed-{s}" in runs]
    if seeds:
        n = len(seeds)
        counts = [sum(r[i][0] for r in seeds) for i in seeds[0]]
        hist = [counts.count(c) for c in range(n + 1)]
        with open(f"{res}/counts.csv", "w") as f:
            f.write("question,correct\n")
            for i, c in zip(seeds[0], counts):
                f.write(f"{i},{c}\n")
        if n > 1:
            s2 = statistics.mean(c * (n - c) / (n * (n - 1))
                                 for c in counts)
            vx = statistics.variance([c / n for c in counts]) - s2 / n
            lines.append(f"Miller: E[sigma^2] = {s2:.4f}, "
                         f"Var(x) = {vx:.4f}")
        lines.append(f"correct samples per question (0..{n}): {hist}")
        with open(f"{res}/passk.csv", "w") as f:
            f.write("k,pass_at_k,pass_hat_k\n")
            for k in (1, 2, 3, 5, 10):
                if k <= n:
                    v = statistics.mean(pass_at_k(n, c, k) for c in counts)
                    w = statistics.mean(math.comb(c, k) / math.comb(n, k)
                                        for c in counts)
                    f.write(f"{k},{v:.3f},{w:.3f}\n")
                    lines.append(f"pass@{k} = {v:.3f}, pass^{k} = {w:.3f}")
        maj = 0
        for i in seeds[0]:
            nums = []
            for r in seeds:
                found = re.findall(r"-?\d[\d,]*(?:\.\d+)?", r[i][1])
                nums.append(found[-1].replace(",", "") if found else "")
            top = Counter(nums).most_common(1)[0][0]
            maj += top != "" and float(top) == float(seeds[0][i][2])
        lines.append(f"majority of {n}: {maj} of {len(seeds[0])}")
        means = [c / n for c in counts]
        se = statistics.stdev(means) / math.sqrt(len(means))
        lines.append(f"mean over seeds {statistics.mean(means):.3f}, "
                     f"stderr over questions {se:.3f}")
    # ------------------------------------------------ quantizations
    names = [x for x in ("chat-Q8_0", "chat-Q4_K_M", "chat-Q4_0")
             if glob.glob(f"{out}/lmeval-{x}/*/samples_*.jsonl")]
    with open(f"{res}/quant.csv", "w") as f:
        f.write("run,filter,correct,n,accuracy,lo,hi,"
                "b_lost,c_gained,diff,diff_lo,diff_hi,mcnemar_p\n")
        for filt in ("number", "flexible-extract", "strict-match"):
            base = lmeval_samples(out, "chat-Q8_0", "gsm8k_chat", filt) \
                if "chat-Q8_0" in names else None
            for x in names:
                s = lmeval_samples(out, x, "gsm8k_chat", filt)
                n, c = len(s), int(sum(s.values()))
                lo, hi = wilson(c, n)
                row = f"{x},{filt},{c},{n},{c/n:.3f},{lo:.3f},{hi:.3f}"
                if base and x != "chat-Q8_0":
                    b = sum(base[i] == 1 and s[i] == 0 for i in s)
                    g = sum(base[i] == 0 and s[i] == 1 for i in s)
                    d = (g - b) / n
                    sd = math.sqrt((b + g) / n - d * d) / math.sqrt(n)
                    row += (f",{b},{g},{d:.3f},{d - Z*sd:.3f},"
                            f"{d + Z*sd:.3f},{mcnemar_p(b, g):.4f}")
                else:
                    row += ",,,,,,"
                f.write(row + "\n")
    for x, task in (("fewshot-Q8_0", "gsm8k"), ("chat-Q8_0", "gsm8k_chat")):
        for filt in ("strict-match", "flexible-extract", "number"):
            try:
                s = lmeval_samples(out, x, task, filt)
            except IndexError:
                continue
            c, n = int(sum(s.values())), len(s)
            lo, hi = wilson(c, n)
            lines.append(f"{x} {filt}: {c}/{n} = {c/n:.3f} "
                         f"[{lo:.3f}, {hi:.3f}]")
    with open(f"{res}/summary.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
