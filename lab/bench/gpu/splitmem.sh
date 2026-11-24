#!/bin/bash
# splitmem.sh GPUS -- how llama.cpp spreads a model over the visible GPUs:
# the memory in use on every card while llama-bench runs.
cd /tmp/scratch; g=$1; tag=$(echo $g | tr -d ,)
CUDA_VISIBLE_DEVICES=$g llama.cpp/build-cuda/bin/llama-bench \
    -m models/Qwen2.5-72B-Instruct-Q4_K_M.gguf -p 512 -n 64 -r 2 -t 8 -ngl 99 \
    -o md > /dev/null 2>&1 &
pid=$!
peak=""
while kill -0 $pid 2>/dev/null; do
  now=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | tr '\n' ' ')
  [ "$(echo $now | tr ' ' '+' | bc)" -gt "$(echo ${peak:-0} | tr ' ' '+' | bc)" ] && peak=$now
  sleep 2
done
{ echo "## largest memory in use (MiB, GPU 0 to 7) while llama-bench ran with CUDA_VISIBLE_DEVICES=$g"
  echo "$peak"; } > rec/llama/split72-gpus$tag.memory.txt
cat rec/llama/split72-gpus$tag.memory.txt
