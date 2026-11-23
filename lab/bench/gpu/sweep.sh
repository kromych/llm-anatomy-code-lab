#!/bin/bash
# sweep.sh NAME PORT MODEL_ID SERVED IN OUT "C1 C2 ..." -- vllm bench serve
# with random prompts of IN tokens and answers of OUT tokens, at each
# concurrency; one JSON file and one line of summary per point.
name=$1; port=$2; model=$3; served=$4; in=$5; out=$6; cs=$7
cd /tmp/scratch; dir=rec/vllm/bench/$name; mkdir -p $dir
export PATH=/tmp/scratch/venv-vllm/bin:$PATH HF_HOME=/tmp/scratch/hf
for c in $cs; do
  min=${MIN_N:-32}; n=$(( c * 4 )); [ $n -lt $min ] && n=$min
  vllm bench serve --backend openai-chat --base-url http://127.0.0.1:$port \
      --endpoint /v1/chat/completions --model $model \
      --served-model-name $served --dataset-name random \
      --random-input-len $in --random-output-len $out --num-prompts $n \
      --max-concurrency $c --request-rate inf --ignore-eos --seed 1 \
      --save-result --result-dir $dir --result-filename c$c.json \
      > $dir/c$c.txt 2>&1
  python3 - $dir/c$c.json $c <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print("C=%-4s done %4d  out %8.1f tok/s  ttft p50 %7.1f ms  tpot p50 %6.2f ms"
      "  itl p50 %6.2f p99 %7.2f ms  %6.1f s" % (
      sys.argv[2], r["completed"], r["output_throughput"],
      r["median_ttft_ms"], r["median_tpot_ms"], r["median_itl_ms"],
      r["p99_itl_ms"], r["duration"]))
PY
done | tee $dir/summary.txt
