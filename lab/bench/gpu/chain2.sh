#!/bin/bash
# chain2.sh -- after chain1: one GPU with vLLM again (long prompts, the
# agent evaluation of Chapter 11, what the server leaves on the system),
# Docker, and the CPU runs (memory bandwidth, instruction-set levels).
cd /tmp/scratch
while ! grep -q "chain1 done" log/chain1.log 2>/dev/null; do sleep 10; done
bin/serve.sh q8-tools2 0 8000 Qwen/Qwen3-8B --served-model-name qwen3-8b default \
    --enable-auto-tool-choice --tool-call-parser hermes --reasoning-parser qwen3 \
    --enable-prompt-tokens-details
{ echo "## ss -ltnp"; ss -ltnp | grep -v ":22 "
  echo "## pstree"; pstree -a -p -T $(cat run/q8-tools2.pid) | cut -c1-150
  echo "## du -sh ~/.cache/vllm/* ~/.cache/flashinfer"; du -sh ~/.cache/vllm/* ~/.cache/flashinfer 2>&1
  echo "## ls /dev/shm"; ls /dev/shm | head -20
  echo "## nvidia-smi --query-compute-apps"; nvidia-smi --query-compute-apps=pid,used_memory --format=csv
} > rec/vllm/footprint.txt 2>&1
MIN_N=16 bin/sweep.sh q8-4096-16 8000 Qwen/Qwen3-8B qwen3-8b 4096 16 "1 8"
MIN_N=8 bin/sweep.sh q8-16384-16 8000 Qwen/Qwen3-8B qwen3-8b 16384 16 "1"
(cd supplement/code/ch11 && AGENT_MODEL=qwen3-8b python3 evaluate.py \
    http://127.0.0.1:8000/v1 5 > /tmp/scratch/rec/vllm/eval-qwen3-8b.jsonl \
    2> /tmp/scratch/rec/vllm/eval-qwen3-8b.txt)
bin/stop.sh q8-tools2
{ echo "## docker run --rm --gpus all ubuntu:24.04 nvidia-smi -L"
  sudo docker run --rm --gpus all ubuntu:24.04 nvidia-smi -L; } > rec/docker-gpu.txt 2>&1
gcc -O3 -march=native -pthread -o run/bw supplement/code/ch08/bw.c
{ echo "# gcc -O3 -march=native -pthread bw.c; numactl --cpunodebind=1 --membind=1 ./bw T"
  for t in 1 2 4 8 16 32 64; do printf "threads %2d  " $t
    numactl --cpunodebind=1 --membind=1 run/bw $t; done; } > rec/bw.txt 2>&1
bin/llama.sh isa-build > log/isa-build.log 2>&1
bin/llama.sh isa-bench 32 > log/isa-bench.log 2>&1
echo "chain2 done $(date -u +%T)"
