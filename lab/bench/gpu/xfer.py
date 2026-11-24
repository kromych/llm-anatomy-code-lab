# xfer.py -- how fast bytes move between host memory and a GPU, and
# between two GPUs. Needs PyTorch with CUDA.
#   python3 xfer.py [GPU_A GPU_B ...]   pairs are (A, B), (A, C), ...
# Host to GPU is timed from pageable and from pinned (page-locked) memory;
# every figure is the best and the median of REPS copies, in GB/s.
import statistics, sys, time
import torch

REPS = 9
SIZES = [1 << 20, 1 << 24, 1 << 28, 1 << 32]   # 1 MiB ... 4 GiB

def timed(copy, dev):
    ts = []
    for _ in range(REPS):
        for d in dev:
            torch.cuda.synchronize(d)
        t = time.perf_counter()
        copy()
        for d in dev:
            torch.cuda.synchronize(d)
        ts.append(time.perf_counter() - t)
    return min(ts), statistics.median(ts)

def rate(n, pair):
    return "%7.2f %7.2f" % (n / pair[0] / 1e9, n / pair[1] / 1e9)

gpus = [int(a) for a in sys.argv[1:]] or [0, 1, 2]
a = gpus[0]
print("torch", torch.__version__, "cuda", torch.version.cuda,
      torch.cuda.get_device_name(a))
print("GB/s, best and median of %d copies" % REPS)
print("%10s  %-22s %15s" % ("bytes", "path", "best  median"))
for n in SIZES:
    page = torch.empty(n, dtype=torch.uint8).fill_(1)
    pin = torch.empty(n, dtype=torch.uint8).fill_(1).pin_memory()
    g = torch.empty(n, dtype=torch.uint8, device=a)
    rows = [("pageable -> gpu%d" % a, lambda: g.copy_(page), [a]),
            ("pinned -> gpu%d" % a,
             lambda: g.copy_(pin, non_blocking=True), [a]),
            ("gpu%d -> pinned" % a,
             lambda: pin.copy_(g, non_blocking=True), [a]),
            ("gpu%d -> pageable" % a, lambda: page.copy_(g), [a])]
    for b in gpus[1:]:
        h = torch.empty(n, dtype=torch.uint8, device=b)
        rows.append(("gpu%d -> gpu%d" % (a, b),
                     lambda h=h: h.copy_(g), [a, b]))
    for name, copy, dev in rows:
        copy()                                   # warm up, fault pages in
        print("%10d  %-22s %s" % (n, name, rate(n, timed(copy, dev))))
    del page, pin, g
