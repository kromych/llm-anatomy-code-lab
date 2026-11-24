# allreduce.py -- the latency of an all-reduce over NCCL, as tensor
# parallelism issues it: every GPU holds a tensor, and afterwards every
# GPU holds the sum. Needs PyTorch with CUDA; start one process per GPU:
#   CUDA_VISIBLE_DEVICES=0,1 torchrun --nproc_per_node 2 allreduce.py
# Rank 0 prints, per message size, the median and the 10th and 90th
# percentiles of the time of one all-reduce and the bytes per second
# that the median corresponds to.
import os, statistics, time
import torch
import torch.distributed as dist

ITERS, WARM = 2000, 200
# rows x hidden size in BF16: one token, 64 sequences, a prefill chunk
SHAPES = [(1, 8192), (64, 8192), (512, 8192), (4096, 8192)]

rank = int(os.environ["LOCAL_RANK"])
torch.cuda.set_device(rank)
dist.init_process_group("nccl")
n = dist.get_world_size()
if rank == 0:
    print("torch", torch.__version__, "nccl",
          ".".join(map(str, torch.cuda.nccl.version())), "gpus", n,
          "visible", os.environ.get("CUDA_VISIBLE_DEVICES"))
    print("%12s %9s %9s %9s %9s" % ("bytes", "p10 us", "median us",
                                    "p90 us", "GB/s"))
for shape in SHAPES:
    x = torch.ones(shape, dtype=torch.bfloat16, device=rank)
    ts = []
    for i in range(WARM + ITERS):
        torch.cuda.synchronize()
        t = time.perf_counter()
        dist.all_reduce(x)
        torch.cuda.synchronize()
        if i >= WARM:
            ts.append(time.perf_counter() - t)
        x.fill_(1)
    if rank == 0:
        q = statistics.quantiles(ts, n=10)
        med = statistics.median(ts)
        size = x.numel() * 2
        print("%12d %9.1f %9.1f %9.1f %9.2f" % (
            size, q[0] * 1e6, med * 1e6, q[-1] * 1e6, size / med / 1e9))
dist.destroy_process_group()
