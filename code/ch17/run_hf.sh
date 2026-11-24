#!/bin/sh
# run_hf.sh -- the in-process run of Chapter 17: lm-eval loads Qwen3-1.7B
# through Transformers and scores two multiple-choice tasks by
# log-likelihood. The command is restored from the configuration that
# lm-eval stored with results/arc-hf-qwen3-1.7b.json and from the log of
# the run; --device mps is Apple's GPU (cuda or cpu elsewhere). Needs torch
# and transformers from requirements.txt in $VENV.
set -u
VENV=${VENV:-venv}; OUT=${OUT:-out-hf}; mkdir -p "$OUT"
"$VENV/bin/lm_eval" --model hf \
  --model_args pretrained=Qwen/Qwen3-1.7B,dtype=bfloat16 \
  --device mps --batch_size 16 --tasks arc_easy,arc_challenge \
  --log_samples --output_path "$OUT/arc" > "$OUT.log" 2>&1
