# sim.py -- static and continuous batching on one GPU (a simulation)
import random

# Cost model: an 8B model in BF16 on one H100
N   = 8.0e9          # parameters
W   = 2 * N          # bytes of weights
KVT = 131072         # bytes of KV cache per token (Llama 3 8B)
B   = 0.8 * 3.35e12  # sustained memory bandwidth, bytes/s
F   = 0.6 * 990e12   # sustained matrix arithmetic, FLOP/s
T0  = 1e-3           # fixed cost per step (launches, scheduling), s

def step(tokens, kv):
    """Seconds for one forward pass over `tokens` new tokens that
    read `kv` cached tokens in total."""
    return T0 + max((W + KVT * kv) / B, 2 * N * tokens / F)

def workload(n, rate, seed=1):
    rng, t, reqs = random.Random(seed), 0.0, []
    for i in range(n):
        t += rng.expovariate(rate)
        reqs.append(dict(id=i, arr=t, p=rng.randint(200, 2000),
                         o=rng.randint(50, 500)))
    return reqs

def static(reqs, bmax=16):
    t, q = 0.0, sorted(reqs, key=lambda r: r["arr"])
    while q:
        t = max(t, q[0]["arr"])
        n = min(bmax, sum(r["arr"] <= t for r in q))
        batch, q = q[:n], q[n:]
        P = max(r["p"] for r in batch)
        for r in batch: r["start"] = t
        t += step(n * P, 0)                      # padded prefill
        for r in batch: r["first"] = r["end"] = t
        for k in range(2, max(r["o"] for r in batch) + 1):
            t += step(n, n * (P + k))            # every slot decodes
            for r in batch:
                if r["o"] >= k: r["end"] = t
        for r in batch: r["free"] = t            # slot released
    return reqs

def continuous(reqs, budget=2048, smax=256, kvcap=450_000):
    t, i, wait, run = 0.0, 0, [], []
    reqs = sorted(reqs, key=lambda r: r["arr"])
    while i < len(reqs) or wait or run:
        if not wait and not run: t = max(t, reqs[i]["arr"])
        while i < len(reqs) and reqs[i]["arr"] <= t:       # L1
            wait.append(reqs[i]); i += 1
        used = sum(r["p"] + r["gen"] for r in run)
        while wait and len(run) < smax and used + wait[0]["p"] <= kvcap:
            r = wait.pop(0); r.update(done=0, gen=0)        # L2
            run.append(r); used += r["p"]
        dec = [r for r in run if r["done"] == r["p"]]       # L3
        tok, kv, left, pre = len(dec), 0, budget - len(dec), []
        for r in dec: kv += r["p"] + r["gen"]
        for r in run:                                       # L4
            if r["done"] < r["p"] and left > 0:
                c = min(left, r["p"] - r["done"])
                pre.append((r, c)); left -= c; tok += c
                kv += r["done"]; r.setdefault("start", t)
        t += step(tok, kv)                                  # L5
        for r, c in pre:
            r["done"] += c
            if r["done"] == r["p"]: r["gen"], r["first"] = 1, t
        for r in dec: r["gen"] += 1
        for r in [r for r in run if r["gen"] == r["o"]]:   # L6
            r["end"] = r["free"] = t; run.remove(r)
    return reqs
