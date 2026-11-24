# times.py -- how long the runs of run_all.sh and run_hf.sh took, from
# the raw logs: the last progress line of lm-eval with the time before and
# after it, the total that lm-eval stores with the results, and the start
# and the end that Inspect stores in a log.
# usage: python3 times.py OUT [LOG...]   (LOG: the log of run_hf.sh)
import glob, json, os, re, sys
from datetime import datetime

BAR = re.compile(r"(Requesting API|Running loglikelihood requests): 100%"
                 r"\S* (\d+)/\2 \[([\d:]+)<")
STAMP = re.compile(r"^(\d{4}-\d\d-\d\d:\d\d:\d\d:\d\d) ")

def stamp(line):
    m = STAMP.match(line)
    return m and datetime.strptime(m.group(1), "%Y-%m-%d:%H:%M:%S")

def seconds(clock):                  # "06:21" or "1:02:03"
    s = 0
    for part in clock.split(":"):
        s = 60 * s + int(part)
    return s

def lmeval(log, results):
    lines = open(log).read().replace("\r", "\n").split("\n")
    stamps = [(i, stamp(l)) for i, l in enumerate(lines) if stamp(l)]
    bars = [(i, m) for i, m in enumerate(map(BAR.search, lines)) if m]
    name = os.path.basename(log)[:-4]
    if not bars:
        return print(f"{name}: no finished progress line")
    i, m = bars[-1]
    n, took = int(m.group(2)), seconds(m.group(3))
    first = stamps[0][1]
    start = [t for j, t in stamps if j < i and "requests" in lines[j]][-1]
    end = [t for j, t in stamps if j > i][0]
    print(f"{name}: {n} requests in {m.group(3)} ({m.group(1)}), "
          f"{took} s, {1000 * took / n:.1f} ms each")
    print(f"  log: {(start - first).seconds} s from the first line to the "
          f"requests, {(end - start).seconds} s from there to the next "
          "line")
    for f in sorted(glob.glob(results)):
        total = float(json.load(open(f))["total_evaluation_time_seconds"])
        print(f"  total_evaluation_time_seconds {total:.1f}")

def inspect(d):
    from inspect_ai.log import read_eval_log
    for f in sorted(glob.glob(f"{d}/*.eval")):
        log = read_eval_log(f)
        a = datetime.fromisoformat(log.stats.started_at)
        b = datetime.fromisoformat(log.stats.completed_at)
        n, took = len(log.samples), (b - a).total_seconds()
        each = sum(s.total_time for s in log.samples) / n
        print(f"{os.path.basename(d)}: {n} samples in {took:.0f} s from "
              f"start to end, {took / n:.2f} s each ({log.status})")
        print(f"  connections {log.plan.config.max_connections}; one "
              f"sample took {each:.2f} s on average")

out = sys.argv[1]
for log in sorted(glob.glob(f"{out}/lmeval-*.log")):
    lmeval(log, f"{log[:-4]}/*/results_*.json")
for d in sorted(glob.glob(f"{out}/inspect-*/")):
    inspect(d.rstrip("/"))
for log in sys.argv[2:]:
    lmeval(log, f"{log[:-4]}/*/*/results_*.json")
