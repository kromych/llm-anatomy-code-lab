#!/bin/bash
# chain4.sh -- after chain3: llama.cpp with a model of 72 billion
# parameters on one GPU and with its layers split over two, four, and eight
# (pipeline parallelism), and the prefix cache of vLLM (Chapter 6).
cd /tmp/scratch
while ! grep -q "chain3 done" log/chain3.log 2>/dev/null; do sleep 10; done
export PATH=$HOME/.local/bin:$PATH HF_HOME=/tmp/scratch/hf
hf download -q bartowski/Qwen2.5-72B-Instruct-GGUF Qwen2.5-72B-Instruct-Q4_K_M.gguf \
    --local-dir models > log/gguf72.log 2>&1
ls -l models/Qwen2.5-72B-Instruct-Q4_K_M.gguf >> log/gguf72.log
B=llama.cpp/build-cuda/bin; M=models/Qwen2.5-72B-Instruct-Q4_K_M.gguf
for g in 0 0,1 0,2 0,1,2,3 0,1,2,3,4,5,6,7; do
  n=$(echo $g | tr , '\n' | wc -l); tag=$(echo $g | tr -d ,)
  o=rec/llama/split72-gpus$tag
  echo "## CUDA_VISIBLE_DEVICES=$g llama-bench -m Qwen2.5-72B-Instruct-Q4_K_M.gguf -p 512 -n 128 -r 3 -t 8 -ngl 99" > $o.txt
  CUDA_VISIBLE_DEVICES=$g $B/llama-bench -m $M -p 512 -n 128 -r 3 -t 8 -ngl 99 \
      -o md >> $o.txt 2> $o.stderr
  grep -E "offloaded|model buffer size|CUDA[0-9] " $o.stderr | head -20 >> $o.txt
  rm -f $o.stderr
done
bin/serve.sh q8-cache 0 8080 Qwen/Qwen3-8B --served-model-name qwen3-8b default \
    --enable-prompt-tokens-details
{ echo "## python3 cachetest.py   (vLLM 0.32.0, Qwen3-8B, port 8080)"
  python3 supplement/code/ch06/code/cachetest.py; } > rec/vllm/cachetest.txt 2>&1
bin/stop.sh q8-cache
echo "chain4 done $(date -u +%T)"
