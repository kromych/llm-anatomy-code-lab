# Runs on a rented machine with eight H100 cards (kr0m-gpu, S5-CloudGPU)

The lab's own machines have no discrete GPU. These are the programs and
records of the runs on a rented one: eight NVIDIA H100 in the PCIe form,
joined in pairs by NVLink, under Ubuntu 24.04 (`lab/hosts/kr0m-gpu` has the
inventory and the notes of the setup). The engines were llama.cpp at commit
61dbf4922 (build 12376), built for CUDA, and vLLM 0.32.0 from its wheel for
CUDA 12.9. In the records the working directory is written `/tmp/scratch`
and the account `labuser`.

| program | what it does |
|---|---|
| `setup.sh` | tools, the two engines, the models |
| `system.sh` | the inventory of the machine |
| `xfer.py` | copy rates between host memory and a GPU, and between two GPUs |
| `rtt_gpu.py` | round trip of a small message between host memory and a GPU |
| `allreduce.py` | the time of an all-reduce over NCCL, for 2, 4 and 8 GPUs |
| `serve.sh`, `stop.sh` | start `vllm serve` on given GPUs and wait until it is ready; stop it |
| `seam.sh` | the probes of Chapters 9 and 10 against a server |
| `sweep.sh` | `vllm bench serve` at a list of concurrencies |
| `tp.sh` | one configuration of tensor parallelism: processes, memory, a short sweep |
| `llama.sh` | llama.cpp: `llama-bench` in the layout of `lab/bench/isa`, the runs for `code/ch07/validate/fit.py`, the scheduler's splits, load times, the CPU builds by instruction set |
| `splitmem.sh` | the memory on each card while llama.cpp runs a model split by layers |
| `chain1.sh` ... `chain5.sh` | the order in which the long runs were made |

## Records (`results/`)

- `xfer.txt`, `rtt_gpu.csv`, `allreduce.txt`: the links. Pinned host
  memory to a GPU 57 GB/s, pageable 20 GB/s; GPU to GPU 265 GB/s over
  NVLink and 38 GB/s through PCIe; an all-reduce of 1 MiB over NCCL 39
  microseconds on a pair joined by NVLink, 154 on eight cards.
- `vllm/install-*.txt`, `vllm/start-without-ninja*.server.log`: what the
  documented installation of vLLM ran into (see the host's notes).
- `vllm/<name>.server.log` (requests left out), `.ps.txt`, `.gpus.txt`,
  and `vllm/bench/<name>/`: one directory per server configuration, with
  the JSON files of `vllm bench serve` and a line per concurrency in
  `summary.txt`. `q8-512-256` is the sweep of one card from 1 to 256
  requests; `q8-tp*` and `q72-tp*` are tensor parallelism with Qwen3-8B
  and Qwen2.5-72B-Instruct; names ending in `-nccl` or `-4k` ran with
  vLLM's fused all-reduce switched off. `q8-tp2-pcie` and `q72-tp2-pcie`
  did not start.
- `vllm/loadgen/`: `loadgen.py` of Chapter 7 against vLLM.
- `vllm/eval-qwen3-8b.*`: `evaluate.py` of Chapter 11 against vLLM.
- `vllm/footprint.txt`: ports, processes and caches of a running server.
- `vllm/cachetest.txt`: `cachetest.py` of Chapter 6 reads llama-server's
  `timings`, which vLLM does not send; kept as the record of that.
- `llama/splits-cuda-*.txt`: `splits.py` of Chapter 8 on the CUDA backend.
- `llama/load-*`: time to load Qwen3-8B Q8_0 with the file in and out of
  the page cache.
- `llama/split72-*`: `llama-bench` with Qwen2.5-72B Q4_K_M on one card and
  with its layers on two, four and eight.
- `docker-gpu.txt`: a container that sees the eight cards.
- `bw.txt`: `bw.c` of Chapter 8 on one processor of the machine.

The runs of `llama-bench` by instruction set are in `lab/bench/isa/kr0m-gpu`,
the runs for the cost model in `lab/bench/validate/batched-bench-h100.txt`
(`python3 code/ch07/validate/fit.py` on that file), the round trips of the
figure of transports in `lab/bench/transport/results/kr0m-gpu-rtt.csv`, and
the probes of the seam in `code/ch09/results/*-vllm*.txt` and
`code/ch10/results/*-vllm*.txt`.
