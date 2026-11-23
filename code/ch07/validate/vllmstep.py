# vllmstep.py DIR W N_PARAMS KVT B F T0 CONTEXT -- set the time between two
# tokens that `vllm bench serve` measured at each concurrency (the files
# DIR/c*.json) against one decode step of sim.py's cost model, with as
# many sequences as there were requests and CONTEXT tokens cached for each.
import glob, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "work"))
import sim

a = sys.argv
sim.W, sim.N, sim.KVT = float(a[2]), float(a[3]), float(a[4])
sim.B, sim.F, sim.T0 = float(a[5]), float(a[6]), float(a[7])
context = float(a[8])
print("requests  tokens/s  gap ms  model ms  ratio")
files = glob.glob(os.path.join(a[1], "c*.json"))
for f in sorted(files, key=lambda f: int(re.findall(r"c(\d+)", f)[-1])):
    r = json.load(open(f))
    c = r["max_concurrency"]
    model = sim.step(c, c * context) * 1e3
    gap = r["median_itl_ms"]
    print("%8d  %8.1f  %6.2f  %8.2f  %5.2f" % (
        c, r["output_throughput"], gap, model, gap / model))
