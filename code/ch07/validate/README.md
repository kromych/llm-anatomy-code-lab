# Checking sim.py against a real server

`sim.py` (in `../work`) replaces each forward pass by the cost model
`step(tokens, kv) = T0 + max((W + KVT*kv)/B, 2*N*tokens/F)`. These scripts fit
the three constants of that model on one device and then compare the
simulation with a real llama-server under the same Poisson workload.

| file | what it does |
|---|---|
| `fit.py` | reads repeated `llama-batched-bench` runs of Gemma 3 1B and Qwen3-8B, keeps the fastest run of each configuration, fits `B` and `T0` from one-sequence decode steps of the two models and `F` from a 2048-token prefill, and prints measured and modelled step and prefill times for every batch size |
| `replay.py` | sends `sim.workload(n, rate, seed)` to llama-server's `/completion` (random token IDs, `ignore_eos`, `cache_prompt: false`) and records arrival, first token and end of every request |
| `compare.py` | runs `sim.continuous` on the same workload with the fitted constants and prints the median and 90th-percentile time to first token, mean latency and throughput, measured and simulated |

Run on krom1u (Apple M1 Ultra, macOS 27.2) with Homebrew llama.cpp b12359 and
`ggml-org/Qwen3-8B-GGUF` `Qwen3-8B-Q8_0.gguf` (8,709,518,656 bytes; Qwen3-8B
has 8.19e9 parameters, 36 layers, 8 KV heads of 128, so an F16 cache takes
147,456 bytes per token):

```sh
for run in 1 2 3; do
  echo "## gemma run $run"; llama-batched-bench -m gemma-3-1b-it-Q4_K_M.gguf \
      -c 4608 -npp 128,2048 -ntg 128 -npl 1 -ngl 99
  echo "## qwen run $run"; llama-batched-bench -m Qwen3-8B-Q8_0.gguf \
      -c 36864 -b 2048 -ub 512 -npp 128,2048 -ntg 128 -npl 1,2,4,8,16 -ngl 99
done > bench.txt 2>&1
python3 fit.py bench.txt
llama-server -m Qwen3-8B-Q8_0.gguf -np 8 -c 32768 --kv-unified -ngl 99 --port 8092
python3 replay.py http://127.0.0.1:8092 40 0.5 1 > replay-0.5.jsonl
python3 compare.py replay-0.5.jsonl 40 0.5 1 8.71e9 8.19e9 147456 B F T0 8 32768
```

The results are in `lab/bench/validate/`.

## The same fit on an H100

On kr0m-gpu (S5-CloudGPU in the book; one NVIDIA H100 PCIe, llama.cpp
b12376 built for CUDA) the three runs of `llama-batched-bench` above are in
`lab/bench/validate/batched-bench-h100.txt`:

```sh
python3 fit.py batched-bench-h100.txt "an H100 PCIe"
# fitted on an H100 PCIe: B = 2029 GB/s, F = 139.1 TFLOP/s, T0 = 1.9 ms
```

`vllmstep.py` sets these constants against vLLM 0.32.0 serving Qwen3-8B in
16-bit weights (16,381,516,776 bytes) on the same card. It reads the files
that `vllm bench serve` wrote at each concurrency
(`lab/bench/gpu/results/vllm/bench/q8-512-256`) and prints, per
concurrency, the tokens per second, the median time between two tokens of
a request, one decode step of the model, and their ratio:

```sh
python3 vllmstep.py q8-512-256 16381516776 8.19e9 147456 2029e9 400e12 1.9e-3 648
```

The 648 is the mean number of cached tokens of a sequence (prompts of 512
random tokens and the 8 of the chat template, answers of 256), and 400e12
the rate at which vLLM processed prompts of 4,096 and 16,384 tokens
(`q8-4096-16`, `q8-16384-16`).
