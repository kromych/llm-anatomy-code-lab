"""Put the questions of common.TASKS to one port and append a line per
answer to a file. Usage: python3 runner.py PORT BASE_URL OUT [TASK...]"""
import importlib, json, sys, time
import common

port, base_url, out = sys.argv[1], sys.argv[2], sys.argv[3]
only = sys.argv[4:]  # optional task ids
tag = base_url.rstrip("/").split("/")[-2]  # the proxy's tag, as port-rN
answer = importlib.import_module(port).make(base_url)
with open(out, "a") as f:
    for tid, question, expected in common.TASKS:
        if only and tid not in only:
            continue
        t0 = time.time()
        try:
            a, err = str(answer(question)), None
        except Exception as e:
            a, err = "", repr(e)[:300]
        rec = {"port": port, "task": tid, "secs": round(time.time() - t0, 2),
               "answer": a[:400], "correct": common.correct(a, expected),
               "error": err, "tag": tag, "t": t0}
        f.write(json.dumps(rec) + "\n")
        print(json.dumps(rec)[:240], flush=True)
