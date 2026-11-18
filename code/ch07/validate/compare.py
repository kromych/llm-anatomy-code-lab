# compare.py RESULTS.jsonl N RATE SEED W N_PARAMS KVT B F T0 [SLOTS CTX]
# Run sim.py's Algorithm L on the same workload with a fitted cost model and
# print the measured and simulated time to first token and throughput.
import json, os, statistics, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "work"))
import sim

a = sys.argv
meas = [json.loads(l) for l in open(a[1])]
n, rate, seed = int(a[2]), float(a[3]), int(a[4])
sim.W, sim.N, sim.KVT = float(a[5]), float(a[6]), float(a[7])
sim.B, sim.F, sim.T0 = float(a[8]), float(a[9]), float(a[10])
slots = int(a[11]) if len(a) > 11 else 8
ctx = int(a[12]) if len(a) > 12 else 32768
simr = sim.continuous(sim.workload(n, rate, seed), budget=2048, smax=slots,
                      kvcap=ctx)

def summary(rs, arr="arr", first="first", end="end"):
    ttft = [r[first] - r[arr] for r in rs]
    lat = [r[end] - r[arr] for r in rs]
    span = max(r[end] for r in rs) - min(r[arr] for r in rs)
    return (statistics.median(ttft), statistics.quantiles(ttft, n=10)[8],
            statistics.mean(lat), sum(r["o"] for r in rs) / span)

for name, s in (("measured", summary(meas)), ("simulated", summary(simr))):
    print(f"{name:9s} TTFT p50 {s[0]:6.2f} s  p90 {s[1]:6.2f} s  "
          f"latency mean {s[2]:6.1f} s  throughput {s[3]:6.1f} tokens/s")
