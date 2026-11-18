# replay.py URL N RATE [SEED] -- send the workload of sim.py to llama-server
# and record, for every request, its arrival, first token and end.
# Prompts are random token IDs, so nothing is found in the prefix cache, and
# ignore_eos makes every answer exactly as long as sim.py says.
import json, os, random, sys, threading, time, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "work"))
import sim

url, n, rate = sys.argv[1] + "/completion", int(sys.argv[2]), float(sys.argv[3])
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
reqs = sim.workload(n, rate, seed)
lock, out = threading.Lock(), []

def one(r, t0):
    rng = random.Random(r["id"])
    body = json.dumps({"prompt": [rng.randrange(1000, 150000) for _ in range(r["p"])],
                       "n_predict": r["o"], "ignore_eos": True, "stream": True,
                       "cache_prompt": False, "temperature": 0}).encode()
    time.sleep(max(0.0, t0 + r["arr"] - time.perf_counter()))
    start, first, k = time.perf_counter() - t0, None, 0
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        for line in resp:
            if line.startswith(b"data: "):
                k += 1
                if first is None: first = time.perf_counter() - t0
    with lock:
        out.append(dict(id=r["id"], p=r["p"], o=r["o"], arr=r["arr"],
                        start=start, first=first, end=time.perf_counter() - t0,
                        chunks=k))

t0 = time.perf_counter()
th = [threading.Thread(target=one, args=(r, t0)) for r in reqs]
for t in th: t.start()
for t in th: t.join()
for r in sorted(out, key=lambda r: r["id"]): print(json.dumps(r))
