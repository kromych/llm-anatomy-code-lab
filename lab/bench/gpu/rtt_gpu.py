# rtt_gpu.py [GPU] -- round trip of a small message between host memory
# and a GPU: copy it from pinned memory to the GPU and back, and wait for
# the GPU to finish. Prints CSV in the form of the other round-trip files.
import statistics, sys, time
import torch

gpu = int(sys.argv[1]) if len(sys.argv) > 1 else 0
N = 2000
print("# %s, torch %s, cuda %s" % (torch.cuda.get_device_name(gpu),
                                   torch.__version__, torch.version.cuda))
print("test,n,median_us,p10_us,p90_us")
for name, size in (("pcie-4k", 4096), ("pcie-1m", 1 << 20)):
    host = torch.ones(size, dtype=torch.uint8).pin_memory()
    back = torch.empty(size, dtype=torch.uint8).pin_memory()
    dev = torch.empty(size, dtype=torch.uint8, device=gpu)
    ts = []
    for i in range(N + 200):
        t = time.perf_counter()
        dev.copy_(host, non_blocking=True)
        back.copy_(dev, non_blocking=True)
        torch.cuda.synchronize(gpu)
        if i >= 200:
            ts.append((time.perf_counter() - t) * 1e6)
    q = statistics.quantiles(ts, n=10)
    print("%s,%d,%.3f,%.3f,%.3f" % (name, N, statistics.median(ts),
                                    q[0], q[-1]))
